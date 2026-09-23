from jobintel import pipeline


def test_daily_digest_runs_after_quality_checks():
    labels = [label for label, _ in pipeline.STEPS]
    assert labels.index("Daily email digest") > labels.index("Data quality checks")


def test_forced_digest_sets_subprocess_env(monkeypatch):
    captured: dict[str, str] = {}

    class Result:
        returncode = 0

    def fake_run(args, *, check, env):
        del args
        del check
        captured.update(env)
        return Result()

    monkeypatch.setattr(pipeline.subprocess, "run", fake_run)

    pipeline.run_step(
        label="Daily email digest",
        module="jobintel.daily_digest",
        run_id=99,
        force_daily_digest=True,
    )

    assert captured["JOBINTEL_DAILY_DIGEST_ENABLED"] == "true"
    assert captured["JOBINTEL_PIPELINE_RUN_ID"] == "99"
