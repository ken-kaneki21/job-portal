from jobintel.pipeline_quality import build_pipeline_quality_snapshot


def test_pipeline_quality_module_is_importable():
    assert callable(build_pipeline_quality_snapshot)
