from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

router = APIRouter(prefix="/auth", tags=["Authentication"])
COOKIE_NAME = "jobintel_session"
SESSION_TTL_SECONDS = int(os.getenv("JOBINTEL_SESSION_TTL_SECONDS", "43200"))
MAX_ATTEMPTS = 8
ATTEMPT_WINDOW_SECONDS = 300
_attempts: dict[str, deque[float]] = defaultdict(deque)


def auth_enabled() -> bool:
    return bool(
        os.getenv("JOBINTEL_AUTH_USERNAME")
        and os.getenv("JOBINTEL_AUTH_PASSWORD")
        and os.getenv("JOBINTEL_SESSION_SECRET")
    )


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _secret() -> bytes:
    value = os.getenv("JOBINTEL_SESSION_SECRET", "")
    if len(value) < 32:
        raise RuntimeError("JOBINTEL_SESSION_SECRET must be at least 32 characters.")
    return value.encode()


def create_session(username: str) -> str:
    payload = json.dumps(
        {"sub": username, "exp": int(time.time()) + SESSION_TTL_SECONDS},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    encoded = _b64(payload)
    signature = _b64(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def verify_session(token: str | None) -> str | None:
    if not token or "." not in token:
        return None
    encoded, signature = token.rsplit(".", 1)
    expected = _b64(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_unb64(encoded))
        if int(payload["exp"]) < int(time.time()):
            return None
        return str(payload["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limited(key: str) -> bool:
    now = time.time()
    queue = _attempts[key]
    while queue and now - queue[0] > ATTEMPT_WINDOW_SECONDS:
        queue.popleft()
    return len(queue) >= MAX_ATTEMPTS


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response):
    if not auth_enabled():
        return {"authenticated": True, "auth_enabled": False}
    key = _client_key(request)
    if _rate_limited(key):
        raise HTTPException(
            status_code=429, detail="Too many login attempts. Try again shortly."
        )
    expected_user = os.environ["JOBINTEL_AUTH_USERNAME"]
    expected_password = os.environ["JOBINTEL_AUTH_PASSWORD"]
    if not (
        hmac.compare_digest(payload.username, expected_user)
        and hmac.compare_digest(payload.password, expected_password)
    ):
        _attempts[key].append(time.time())
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    _attempts.pop(key, None)
    secure = os.getenv("JOBINTEL_COOKIE_SECURE", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    response.set_cookie(
        COOKIE_NAME,
        create_session(payload.username),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=secure,
        samesite="none" if secure else "lax",
        path="/",
    )
    return {"authenticated": True, "auth_enabled": True, "username": payload.username}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"authenticated": False}


@router.get("/me")
def me(request: Request):
    if not auth_enabled():
        return {"authenticated": True, "auth_enabled": False}
    username = verify_session(request.cookies.get(COOKIE_NAME))
    if username is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return {"authenticated": True, "auth_enabled": True, "username": username}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if (
            not auth_enabled()
            or request.method == "OPTIONS"
            or request.url.path in {"/", "/health", "/auth/login"}
            or request.url.path.startswith("/companion/")
        ):
            return await call_next(request)
        if verify_session(request.cookies.get(COOKIE_NAME)) is None:
            return JSONResponse(
                status_code=401, content={"detail": "Authentication required."}
            )
        return await call_next(request)
