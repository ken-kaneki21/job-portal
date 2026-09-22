from jobintel.system_readiness import ReadinessResult


def test_readiness_result_serializes():
    result = ReadinessResult(
        ready=True,
        database="connected",
        profile="available",
        profile_name="universal",
    )

    assert result.to_dict() == {
        "ready": True,
        "database": "connected",
        "profile": "available",
        "profile_name": "universal",
    }
