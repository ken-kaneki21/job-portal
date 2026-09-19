from html import escape


def build_job_email(
    *,
    title: str,
    company: str,
    location: str | None,
    score: float,
    apply_url: str,
) -> tuple[str, str]:
    safe_title = escape(title)

    safe_company = escape(company)

    safe_location = escape(location or "Unknown")

    safe_url = escape(
        apply_url,
        quote=True,
    )

    subject = f"New high-confidence job: {title} at {company}"

    html = f"""
    <html>
        <body>
            <h2>New high-confidence job</h2>

            <p>
                <strong>Role:</strong>
                {safe_title}
            </p>

            <p>
                <strong>Company:</strong>
                {safe_company}
            </p>

            <p>
                <strong>Location:</strong>
                {safe_location}
            </p>

            <p>
                <strong>Match score:</strong>
                {score:.1f}/100
            </p>

            <p>
                <a href="{safe_url}">
                    Apply to this job
                </a>
            </p>
        </body>
    </html>
    """

    return (
        subject,
        html,
    )
