def build_job_text(
    job,
) -> str:
    parts = [
        f"Job title: {job.title}",
        f"Company: {job.company}",
    ]

    if job.location:
        parts.append(
            f"Location: {job.location}"
        )

    if job.department:
        parts.append(
            f"Department: {job.department}"
        )

    if job.description:
        description = (
            job.description[:12000]
        )

        parts.append(
            "Job description:\n"
            + description
        )

    return "\n".join(
        parts
    )