from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


class ResumeParseError(
    ValueError,
):
    pass


def build_reader(
    content: bytes,
) -> PdfReader:
    if not content:
        raise ResumeParseError(
            "Resume file is empty.",
        )

    try:
        return PdfReader(
            BytesIO(content),
        )
    except Exception as exc:
        raise ResumeParseError(
            "Unable to read resume PDF.",
        ) from exc


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
        return page.extract_text() or ""
    except Exception:
        return ""


def extract_pdf_text(
    content: bytes,
) -> str:
    reader = build_reader(
        content,
    )

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


def resolve_pdf_object(
    value,
):
    if hasattr(
        value,
        "get_object",
    ):
        try:
            return value.get_object()
        except Exception:
            return value

    return value


def extract_pdf_links(
    content: bytes,
) -> list[str]:
    reader = build_reader(
        content,
    )

    links: list[str] = []
    seen: set[str] = set()

    for page in reader.pages:
        annotations = (
            page.get(
                "/Annots",
            )
            or []
        )

        for annotation in annotations:
            annotation_object = resolve_pdf_object(
                annotation,
            )

            if not hasattr(
                annotation_object,
                "get",
            ):
                continue

            if annotation_object.get("/Subtype") != "/Link":
                continue

            action = resolve_pdf_object(annotation_object.get("/A"))

            if not hasattr(
                action,
                "get",
            ):
                continue

            if action.get("/S") != "/URI":
                continue

            uri = action.get("/URI")

            if uri is None:
                continue

            cleaned = str(uri).strip()

            if not cleaned:
                continue

            if cleaned in seen:
                continue

            seen.add(cleaned)

            links.append(cleaned)

    return links
