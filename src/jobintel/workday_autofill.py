from __future__ import annotations

import argparse
import re
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
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=None,
        help="Optional screenshot path captured after autofill for debugging.",
    )
    return parser.parse_args()


def try_fill_locator(locator, value: str) -> bool:
    try:
        if locator.count() <= 0:
            return False

        element = locator.first
        if not element.is_visible():
            return False

        tag = element.evaluate("el => el.tagName.toLowerCase()")
        if tag == "select":
            try:
                element.select_option(label=value)
            except Exception:
                element.select_option(value=value)
        else:
            element.fill(value)

        return True
    except Exception:
        return False


def fill_by_label(page, field: WorkdayField) -> bool:
    for label in field.labels:
        if try_fill_locator(page.get_by_label(label, exact=False), field.value):
            return True
    return False


def fill_by_placeholder(page, field: WorkdayField) -> bool:
    for label in field.labels:
        if try_fill_locator(page.get_by_placeholder(label, exact=False), field.value):
            return True
    return False


def fill_by_attribute(page, field: WorkdayField) -> bool:
    candidates = {
        field.key,
        *(label.lower().replace(" ", "_") for label in field.labels),
    }

    for candidate in candidates:
        safe = re.sub(r"[^a-z0-9_-]", "", candidate.lower())
        for selector in (
            f'input[name*="{safe}" i]',
            f'textarea[name*="{safe}" i]',
            f'input[id*="{safe}" i]',
            f'textarea[id*="{safe}" i]',
        ):
            if try_fill_locator(page.locator(selector), field.value):
                return True

    return False


def fill_field(page, field: WorkdayField) -> bool:
    return (
        fill_by_label(page, field)
        or fill_by_placeholder(page, field)
        or fill_by_attribute(page, field)
    )


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


def required_unfilled(page) -> list[str]:
    results: list[str] = []

    for selector in (
        "input[required]",
        "textarea[required]",
        "select[required]",
        '[aria-required="true"]',
    ):
        try:
            locator = page.locator(selector)
            for index in range(locator.count()):
                element = locator.nth(index)
                if not element.is_visible():
                    continue

                try:
                    value = element.input_value()
                except Exception:
                    value = ""

                if str(value).strip():
                    continue

                label = (
                    element.get_attribute("aria-label")
                    or element.get_attribute("name")
                    or element.get_attribute("id")
                    or "required field"
                )

                if label not in results:
                    results.append(label)
        except Exception:
            continue

    return results


def final_submit_visible(page) -> bool:
    patterns = (
        re.compile(r"^submit$", re.I),
        re.compile(r"submit application", re.I),
    )

    for pattern in patterns:
        try:
            locator = page.get_by_role("button", name=pattern)
            if locator.count() > 0 and locator.first.is_visible():
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
        review_fields: list[str] = []

        for field in plan.fields:
            if field.review_required:
                review_fields.append(field.key)

            if fill_field(page, field):
                filled.append(field.key)
            else:
                skipped.append(field.key)

        resume_uploaded = False
        if args.resume is not None:
            resume_uploaded = upload_resume(page, args.resume)

        missing_required = required_unfilled(page)
        submit_visible = final_submit_visible(page)

        if args.screenshot is not None:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(args.screenshot), full_page=True)

        print("Filled: " + (", ".join(filled) if filled else "none"))
        print("Needs manual review: " + (", ".join(skipped) if skipped else "none"))

        if review_fields:
            print("Decision-sensitive fields: " + ", ".join(review_fields))

        if args.resume is not None:
            print("Resume uploaded: " + str(resume_uploaded))

        if missing_required:
            print("Required fields still empty: " + ", ".join(missing_required))

        print("Final submit visible: " + str(submit_visible))
        print()
        print("Review the application in the browser.")
        print("This tool WILL NOT click the final Submit button.")
        print("Navigate additional Workday steps manually as needed.")
        print("After you manually submit, mark the job as applied.")

        input(
            "\nPress Enter here when you are finished reviewing the browser session..."
        )
        browser.close()


if __name__ == "__main__":
    main()
