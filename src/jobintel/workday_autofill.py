from __future__ import annotations

import argparse
from pathlib import Path

from jobintel.application_workflow.packet import build_application_packet
from jobintel.application_workflow.workday import (
    WorkdayField,
    build_workday_plan,
)
from jobintel.db.session import SessionLocal
from jobintel.resume.service import load_universal_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Open a Workday application in a headed browser, fill supported "
            "fields, optionally upload a resume, and stop for manual review. "
            "This command never clicks Submit."
        )
    )
    parser.add_argument("--job-id", type=int, required=True)
    parser.add_argument("--resume", type=Path, default=None)
    return parser.parse_args()


def fill_by_label(page, field: WorkdayField) -> bool:
    for label in field.labels:
        try:
            locator = page.get_by_label(label, exact=False)
            if locator.count() <= 0:
                continue
            element = locator.first
            if not element.is_visible():
                continue
            element.fill(field.value)
            return True
        except Exception:
            continue
    return False


def upload_resume(page, resume: Path) -> bool:
    if not resume.exists():
        raise FileNotFoundError(str(resume))

    for selector in (
        "input[type=file]",
        "input[accept*='pdf']",
        "input[accept*='doc']",
    ):
        try:
            locator = page.locator(selector)
            if locator.count() <= 0:
                continue
            locator.first.set_input_files(str(resume.resolve()))
            return True
        except Exception:
            continue
    return False


def main() -> None:
    args = parse_args()

    profile = load_universal_profile()
    if profile is None:
        raise RuntimeError("Universal candidate profile was not found.")

    with SessionLocal() as session:
        packet = build_application_packet(
            session=session,
            job_id=args.job_id,
            profile=profile,
        )

    plan = build_workday_plan(packet)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run: "
            'pip install -e ".[automation]" && '
            "python -m playwright install chromium"
        ) from exc

    print(f"Opening: {plan.apply_url}")
    print("Autofill will stop before final submission.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(plan.apply_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        filled: list[str] = []
        skipped: list[str] = []

        for field in plan.fields:
            if fill_by_label(page, field):
                filled.append(field.key)
            else:
                skipped.append(field.key)

        resume_uploaded = False
        if args.resume is not None:
            resume_uploaded = upload_resume(page, args.resume)

        print("Filled: " + (", ".join(filled) if filled else "none"))
        print("Needs manual review: " + (", ".join(skipped) if skipped else "none"))

        if args.resume is not None:
            print("Resume uploaded: " + str(resume_uploaded))

        print()
        print("Review the application in the browser.")
        print("This tool WILL NOT click the final Submit button.")
        print(
            "After you manually submit, mark the job as applied "
            "through the existing API/UI."
        )

        input(
            "\nPress Enter here when you are finished reviewing the browser session..."
        )
        browser.close()


if __name__ == "__main__":
    main()
