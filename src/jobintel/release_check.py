from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import text

from jobintel.db.profile_repository import get_universal_profile_payload
from jobintel.db.session import SessionLocal
from jobintel.profile.runtime import ACTIVE_PROFILE_NAME
from jobintel.version import __version__

ROOT = Path.cwd()


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


def command(*args: str) -> tuple[int, str]:
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode, result.stdout.strip()


def result(name: str, status: str, detail: str) -> CheckResult:
    return CheckResult(name=name, status=status, detail=detail)


def tracked_paths() -> set[str]:
    code, output = command("git", "ls-files")
    if code != 0:
        return set()
    return {
        value.strip().replace("\\", "/")
        for value in output.splitlines()
        if value.strip()
    }


def check_git_clean(*, allow_dirty: bool) -> CheckResult:
    code, output = command("git", "status", "--short")
    if code != 0:
        return result("git", "fail", output or "Unable to inspect git status.")
    if not output:
        return result("git", "pass", "Working tree is clean.")
    if allow_dirty:
        return result(
            "git",
            "warn",
            "Working tree is dirty, allowed for this validation run.",
        )
    return result("git", "fail", "Working tree must be clean before release.")


def check_sensitive_tracking() -> CheckResult:
    tracked = {value.lower() for value in tracked_paths()}
    forbidden = {
        ".env",
        "profiles/universal.json",
        "profiles/generated_v2.json",
    }
    violations = sorted(forbidden & tracked)

    if violations:
        return result(
            "sensitive-files",
            "fail",
            "Tracked sensitive files: " + ", ".join(violations),
        )

    return result(
        "sensitive-files",
        "pass",
        "Runtime .env and candidate profile JSON files are not tracked.",
    )


def check_migrations() -> CheckResult:
    current_code, current = command("alembic", "current")
    heads_code, heads = command("alembic", "heads")

    if current_code != 0 or heads_code != 0:
        return result(
            "migrations",
            "fail",
            "Unable to inspect Alembic state.",
        )

    current_ids = {
        token.split("(")[0]
        for line in current.splitlines()
        for token in line.split()
        if token and token[0].isalnum()
    }
    head_ids = {line.split()[0] for line in heads.splitlines() if line.strip()}

    if not head_ids or not (head_ids & current_ids):
        return result(
            "migrations",
            "fail",
            f"Database is not at Alembic head. current={current!r}, heads={heads!r}",
        )

    return result("migrations", "pass", "Database migration is at head.")


def check_database() -> CheckResult:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
            profile = get_universal_profile_payload(
                session,
                profile_name=ACTIVE_PROFILE_NAME,
            )
    except Exception as exc:
        return result("database", "fail", f"Database check failed: {exc}")

    if profile is None:
        return result(
            "database",
            "fail",
            "Database is connected but the active universal profile is missing.",
        )

    return result(
        "database",
        "pass",
        "Database connected and active candidate profile is available.",
    )


def check_python_dependencies() -> CheckResult:
    code, output = command(sys.executable, "-m", "pip", "check")
    if code != 0:
        return result("python-dependencies", "fail", output)

    return result(
        "python-dependencies",
        "pass",
        output or "Python dependency graph is consistent.",
    )


def check_docker_compose() -> CheckResult:
    candidates = [
        ROOT / name
        for name in (
            "compose.yml",
            "compose.yaml",
            "docker-compose.yml",
            "docker-compose.yaml",
        )
        if (ROOT / name).exists()
    ]

    if not candidates:
        return result("docker-compose", "warn", "No Compose file found.")

    docker = shutil.which("docker")
    if docker is None:
        return result(
            "docker-compose",
            "warn",
            "Docker CLI is not available in this shell.",
        )

    for path in candidates:
        code, output = command(
            docker,
            "compose",
            "-f",
            str(path),
            "config",
            "--quiet",
        )
        if code != 0:
            return result(
                "docker-compose",
                "fail",
                output or f"Invalid Compose file: {path.name}",
            )

    return result(
        "docker-compose",
        "pass",
        "Docker Compose configuration is valid.",
    )


def check_precommit_configuration() -> CheckResult:
    path = ROOT / ".pre-commit-config.yaml"

    if not path.exists():
        return result(
            "pre-commit-config",
            "fail",
            ".pre-commit-config.yaml is missing.",
        )

    content = path.read_text(encoding="utf-8")

    if "id: ruff-format" in content:
        return result(
            "pre-commit-config",
            "fail",
            "ruff-format is still configured alongside Black.",
        )

    return result(
        "pre-commit-config",
        "pass",
        "Black is the single formatter; Ruff remains the linter.",
    )


def check_env_example() -> CheckResult:
    path = ROOT / ".env.example"

    if not path.exists():
        return result(
            "env-example",
            "warn",
            ".env.example is missing.",
        )

    suspicious: list[str] = []

    for line in path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        value = line.strip()

        if not value or value.startswith("#") or "=" not in value:
            continue

        key, raw = value.split("=", 1)
        raw = raw.strip()

        if (
            raw
            and not raw.startswith(("${", "<", "your_", "change"))
            and key.upper().endswith(("_KEY", "_TOKEN", "_SECRET", "_PASSWORD"))
        ):
            suspicious.append(key)

    if suspicious:
        return result(
            "env-example",
            "fail",
            "Potential populated secrets in .env.example: " + ", ".join(suspicious),
        )

    return result(
        "env-example",
        "pass",
        ".env.example contains no obvious populated secrets.",
    )


def run_checks(*, allow_dirty: bool) -> list[CheckResult]:
    return [
        check_git_clean(allow_dirty=allow_dirty),
        check_sensitive_tracking(),
        check_migrations(),
        check_database(),
        check_python_dependencies(),
        check_docker_compose(),
        check_precommit_configuration(),
        check_env_example(),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Job Intelligence V2 production release gate."
    )
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_checks(allow_dirty=args.allow_dirty)
    failed = [item for item in results if item.status == "fail"]

    if args.json:
        print(
            json.dumps(
                {
                    "version": __version__,
                    "release_ready": not failed,
                    "checks": [item.to_dict() for item in results],
                },
                indent=2,
            )
        )
    else:
        print(f"Job Intelligence {__version__}")
        print("=" * 72)

        for item in results:
            print(f"[{item.status.upper():4}] " f"{item.name}: {item.detail}")

        print("=" * 72)
        print("Release gate: " + ("PASS" if not failed else "FAIL"))

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
