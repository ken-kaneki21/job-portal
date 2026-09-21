from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


class ResumeParseError(
    ValueError,
):
    pass


def extract_page_text(
    page,
) -> str:
    try:
        return (
            page.extract_text(
                extraction_mode="layout",
            )
            or ""
        )
    except TypeError:
        # Compatibility fallback for older pypdf
        # versions that do not support layout mode.
        return page.extract_text() or ""
    except Exception:
        return ""


def extract_pdf_text(
    content: bytes,
) -> str:
    if not content:
        raise ResumeParseError(
            "Resume file is empty.",
        )

    try:
        reader = PdfReader(
            BytesIO(content),
        )
    except Exception as exc:
        raise ResumeParseError(
            "Unable to read resume PDF.",
        ) from exc

    parts: list[str] = []

    for page in reader.pages:
        text = extract_page_text(
            page,
        )

        cleaned = text.strip()

        if cleaned:
            parts.append(
                cleaned,
            )

    result = "\n\n".join(
        parts,
    ).strip()

    if not result:
        raise ResumeParseError(
            "No readable text was found in the resume.",
        )

    return result
