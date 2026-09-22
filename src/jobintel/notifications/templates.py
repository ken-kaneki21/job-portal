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


def build_daily_digest_email(
    *,
    jobs: list[dict],
    pipeline_run_id: int,
) -> tuple[str, str]:
    safe_rows = []

    for job in jobs:
        safe_title = escape(str(job["title"]))
        safe_company = escape(str(job["company"]))
        safe_location = escape(str(job.get("location") or "Unknown"))
        safe_url = escape(
            str(job["apply_url"]),
            quote=True,
        )
        score = float(job["score"])
        bucket = escape(str(job["bucket"]).replace("_", " ").title())

        safe_rows.append(
            f"""
            <tr>
                <td style="padding:14px 10px;border-bottom:1px solid #e8ecef;">
                    <strong>{safe_title}</strong><br>
                    <span>{safe_company} · {safe_location}</span>
                </td>
                <td style="padding:14px 10px;border-bottom:1px solid #e8ecef;">
                    {score:.1f}
                </td>
                <td style="padding:14px 10px;border-bottom:1px solid #e8ecef;">
                    {bucket}
                </td>
                <td style="padding:14px 10px;border-bottom:1px solid #e8ecef;">
                    <a href="{safe_url}">Open job</a>
                </td>
            </tr>
            """
        )

    subject = (
        f"Job Intelligence daily digest · run {pipeline_run_id} "
        f"· {len(jobs)} opportunities"
    )

    html = f"""
    <html>
        <body style="font-family:Arial,sans-serif;color:#172026;">
            <h2>Daily Job Intelligence</h2>
            <p>
                Top fresh opportunities from pipeline run
                <strong>#{pipeline_run_id}</strong>.
            </p>
            <table
                style="width:100%;border-collapse:collapse;"
                cellpadding="0"
                cellspacing="0"
            >
                <thead>
                    <tr>
                        <th align="left" style="padding:10px;">Opportunity</th>
                        <th align="left" style="padding:10px;">Match</th>
                        <th align="left" style="padding:10px;">Bucket</th>
                        <th align="left" style="padding:10px;">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(safe_rows)}
                </tbody>
            </table>
        </body>
    </html>
    """

    return subject, html
