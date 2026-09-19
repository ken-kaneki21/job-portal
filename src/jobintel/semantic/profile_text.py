def build_profile_text(
    profile,
) -> str:
    sections = []

    target_titles = getattr(
        profile,
        "target_titles",
        [],
    )

    adjacent_titles = getattr(
        profile,
        "adjacent_titles",
        [],
    )

    core_skills = getattr(
        profile,
        "core_skills",
        [],
    )

    secondary_skills = getattr(
        profile,
        "secondary_skills",
        [],
    )

    preferred_locations = getattr(
        profile,
        "preferred_locations",
        [],
    )

    if target_titles:
        sections.append(
            "Target roles: "
            + ", ".join(
                target_titles
            )
        )

    if adjacent_titles:
        sections.append(
            "Related roles: "
            + ", ".join(
                adjacent_titles
            )
        )

    if core_skills:
        sections.append(
            "Core technical skills: "
            + ", ".join(
                core_skills
            )
        )

    if secondary_skills:
        sections.append(
            "Additional skills: "
            + ", ".join(
                secondary_skills
            )
        )

    if preferred_locations:
        sections.append(
            "Preferred locations: "
            + ", ".join(
                preferred_locations
            )
        )

    sections.append(
        "Data engineering work involving "
        "ETL and ELT pipelines, cloud data "
        "platforms, data warehouses, Python, "
        "SQL, distributed processing, "
        "orchestration, data modelling, "
        "data quality and production systems."
    )

    return "\n".join(
        sections
    )