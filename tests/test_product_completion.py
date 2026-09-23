from jobintel.product_completion_api import extract_hiring_post


def test_extract_hiring_post() -> None:
    result = extract_hiring_post(
        (
            "We are hiring Data Engineer at Example Labs in Bengaluru. "
            "Looking for 3+ years with Python, SQL, Snowflake and dbt. "
            "Apply via recruiter@example.com"
        ),
        "https://www.linkedin.com/posts/example",
    )

    assert result["role"] == "Data Engineer"
    assert result["location"] == "Bengaluru"
    assert result["minimum_experience_years"] == 3
    assert "python" in result["skills"]
    assert "sql" in result["skills"]
    assert "snowflake" in result["skills"]
    assert "dbt" in result["skills"]
    assert result["contact_emails"] == ["recruiter@example.com"]
    assert result["review_required"] is True
    assert result["auto_apply"] is False
