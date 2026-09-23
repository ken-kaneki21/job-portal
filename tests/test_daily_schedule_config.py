import pytest

from jobintel.temporal_pipeline.schedule_config import (
    DailyScheduleConfig,
    build_schedule_note,
    parse_schedule_note,
)


def test_schedule_note_round_trip():
    config = DailyScheduleConfig(
        hour=8,
        minute=30,
        timezone="Asia/Kolkata",
        send_digest=True,
    )
    restored = parse_schedule_note(build_schedule_note(config))
    assert restored == config


def test_schedule_config_rejects_invalid_hour():
    with pytest.raises(ValueError, match="hour"):
        DailyScheduleConfig(
            hour=25,
            minute=0,
            timezone="UTC",
        ).validate()


def test_invalid_note_falls_back_to_defaults():
    restored = parse_schedule_note("not-json")
    assert restored.hour == 8
    assert restored.minute == 0
    assert restored.send_digest is True
