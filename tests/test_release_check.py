from jobintel.release_check import CheckResult, result


def test_release_check_result_helper():
    passed = result(
        "example",
        "pass",
        "ok",
    )

    assert isinstance(
        passed,
        CheckResult,
    )
    assert passed.status == "pass"
