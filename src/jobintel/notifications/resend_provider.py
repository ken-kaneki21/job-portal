import os
from typing import Any, cast

import resend
from dotenv import load_dotenv

load_dotenv()


def send_email(
    *,
    subject: str,
    html: str,
    idempotency_key: str,
) -> str:
    api_key = os.getenv("RESEND_API_KEY")

    from_email = os.getenv("NOTIFICATION_FROM_EMAIL")

    to_email = os.getenv("NOTIFICATION_TO_EMAIL")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured.")

    if not from_email:
        raise RuntimeError("NOTIFICATION_FROM_EMAIL is not configured.")

    if not to_email:
        raise RuntimeError("NOTIFICATION_TO_EMAIL is not configured.")

    resend.api_key = api_key

    params = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    response = resend.Emails.send(
        cast(Any, params),
        {"idempotency_key": (idempotency_key)},
    )

    email_id = getattr(
        response,
        "id",
        None,
    )

    if email_id is None:
        if isinstance(
            response,
            dict,
        ):
            email_id = response.get("id")

    if not email_id:
        raise RuntimeError("Resend returned no email ID.")

    return str(email_id)
