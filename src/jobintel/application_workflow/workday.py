from __future__ import annotations

from dataclasses import asdict, dataclass

from jobintel.application_workflow.packet import ApplicationPacket


@dataclass(frozen=True)
class WorkdayField:
    key: str
    value: str
    labels: tuple[str, ...]
    sensitive: bool = False


@dataclass(frozen=True)
class WorkdayPlan:
    apply_url: str
    fields: tuple[WorkdayField, ...]
    review_required: bool = True
    submit_action_enabled: bool = False

    def to_dict(self) -> dict:
        return {
            "apply_url": self.apply_url,
            "fields": [asdict(field) for field in self.fields],
            "review_required": self.review_required,
            "submit_action_enabled": self.submit_action_enabled,
        }


def add_field(
    fields: list[WorkdayField],
    *,
    key: str,
    value,
    labels: tuple[str, ...],
    sensitive: bool = False,
) -> None:
    if value is None:
        return
    cleaned = str(value).strip()
    if not cleaned:
        return
    fields.append(
        WorkdayField(
            key=key,
            value=cleaned,
            labels=labels,
            sensitive=sensitive,
        )
    )


def build_workday_plan(packet: ApplicationPacket) -> WorkdayPlan:
    answers = packet.answers
    fields: list[WorkdayField] = []

    add_field(
        fields,
        key="first_name",
        value=answers.get("first_name"),
        labels=("First Name", "Given Name"),
    )
    add_field(
        fields,
        key="last_name",
        value=answers.get("last_name"),
        labels=("Last Name", "Family Name", "Surname"),
    )
    add_field(
        fields,
        key="email",
        value=answers.get("email"),
        labels=("Email", "Email Address"),
        sensitive=True,
    )
    add_field(
        fields,
        key="phone",
        value=answers.get("phone"),
        labels=("Phone", "Phone Number", "Mobile"),
        sensitive=True,
    )
    add_field(
        fields,
        key="location",
        value=answers.get("current_location"),
        labels=("Location", "City", "Current Location"),
    )
    add_field(
        fields,
        key="linkedin",
        value=answers.get("linkedin_url"),
        labels=("LinkedIn", "LinkedIn Profile", "LinkedIn URL"),
    )
    add_field(
        fields,
        key="github",
        value=answers.get("github_url"),
        labels=("GitHub", "GitHub Profile", "GitHub URL"),
    )
    add_field(
        fields,
        key="portfolio",
        value=answers.get("portfolio_url"),
        labels=("Portfolio", "Website", "Personal Website"),
    )
    add_field(
        fields,
        key="current_company",
        value=answers.get("current_company"),
        labels=("Current Company", "Current Employer", "Employer"),
    )
    add_field(
        fields,
        key="current_title",
        value=answers.get("current_title"),
        labels=("Current Title", "Job Title", "Current Job Title"),
    )
    add_field(
        fields,
        key="experience",
        value=answers.get("total_experience_years"),
        labels=("Years of Experience", "Total Experience"),
    )

    return WorkdayPlan(apply_url=packet.apply_url, fields=tuple(fields))
