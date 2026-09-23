from __future__ import annotations

import json
from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_DAILY_HOUR = 8
DEFAULT_DAILY_MINUTE = 0
DEFAULT_TIMEZONE = "Asia/Kolkata"


@dataclass(frozen=True)
class DailyScheduleConfig:
    hour: int = DEFAULT_DAILY_HOUR
    minute: int = DEFAULT_DAILY_MINUTE
    timezone: str = DEFAULT_TIMEZONE
    send_digest: bool = True

    def validate(self) -> DailyScheduleConfig:
        if not 0 <= self.hour <= 23:
            raise ValueError("hour must be between 0 and 23.")

        if not 0 <= self.minute <= 59:
            raise ValueError("minute must be between 0 and 59.")

        timezone = self.timezone.strip()

        if not timezone:
            raise ValueError("timezone is required.")

        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown IANA timezone: {timezone}") from exc

        return DailyScheduleConfig(
            hour=self.hour,
            minute=self.minute,
            timezone=timezone,
            send_digest=self.send_digest,
        )


def build_schedule_note(config: DailyScheduleConfig) -> str:
    validated = config.validate()

    return json.dumps(
        {
            "kind": "jobintel-daily-pipeline",
            "hour": validated.hour,
            "minute": validated.minute,
            "timezone": validated.timezone,
            "send_digest": validated.send_digest,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def parse_schedule_note(note: str | None) -> DailyScheduleConfig:
    if not note:
        return DailyScheduleConfig()

    try:
        payload = json.loads(note)
    except json.JSONDecodeError:
        return DailyScheduleConfig()

    if not isinstance(payload, dict):
        return DailyScheduleConfig()

    try:
        config = DailyScheduleConfig(
            hour=int(payload.get("hour", DEFAULT_DAILY_HOUR)),
            minute=int(payload.get("minute", DEFAULT_DAILY_MINUTE)),
            timezone=str(payload.get("timezone", DEFAULT_TIMEZONE)),
            send_digest=bool(payload.get("send_digest", True)),
        )
        return config.validate()
    except (TypeError, ValueError):
        return DailyScheduleConfig()
