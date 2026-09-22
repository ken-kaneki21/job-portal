from __future__ import annotations

import jobintel.resume.parser as parser_module
from jobintel.profile.universal import (
    CandidateIdentity,
)
from jobintel.resume.service import (
    classify_profile_links,
    enrich_identity_with_pdf_links,
)


class FakeIndirectObject:
    def __init__(
        self,
        payload,
    ):
        self.payload = payload

    def get_object(
        self,
    ):
        return self.payload


class FakePage:
    def __init__(
        self,
        annotations,
    ):
        self.annotations = annotations

    def get(
        self,
        key,
    ):
        if key == "/Annots":
            return self.annotations

        return None


class FakeReader:
    def __init__(
        self,
        pages,
    ):
        self.pages = pages


def test_extract_pdf_links(
    monkeypatch,
):
    linkedin = {
        "/Subtype": "/Link",
        "/A": {
            "/S": "/URI",
            "/URI": ("https://www.linkedin.com/in/example-profile/"),
        },
    }

    github = {
        "/Subtype": "/Link",
        "/A": {
            "/S": "/URI",
            "/URI": ("https://github.com/example-user"),
        },
    }

    ignored = {
        "/Subtype": "/Text",
    }

    fake_reader = FakeReader(
        pages=[
            FakePage(
                annotations=[
                    FakeIndirectObject(linkedin),
                    FakeIndirectObject(github),
                    FakeIndirectObject(ignored),
                ]
            )
        ]
    )

    monkeypatch.setattr(
        parser_module,
        "build_reader",
        lambda content: fake_reader,
    )

    links = parser_module.extract_pdf_links(b"fake-pdf")

    assert links == [
        ("https://www.linkedin.com/in/example-profile/"),
        ("https://github.com/example-user"),
    ]


def test_extract_pdf_links_deduplicates(
    monkeypatch,
):
    annotation = {
        "/Subtype": "/Link",
        "/A": {
            "/S": "/URI",
            "/URI": ("https://example.com"),
        },
    }

    fake_reader = FakeReader(
        pages=[
            FakePage(
                annotations=[
                    FakeIndirectObject(annotation),
                    FakeIndirectObject(annotation),
                ]
            )
        ]
    )

    monkeypatch.setattr(
        parser_module,
        "build_reader",
        lambda content: fake_reader,
    )

    links = parser_module.extract_pdf_links(b"fake-pdf")

    assert links == ["https://example.com"]


def test_classify_profile_links():
    (
        linkedin,
        github,
        portfolio,
    ) = classify_profile_links(
        [
            ("https://github.com/example-user"),
            ("https://example.dev"),
            ("https://www.linkedin.com/in/example-profile/"),
        ]
    )

    assert linkedin == ("https://www.linkedin.com/in/example-profile/")

    assert github == ("https://github.com/example-user")

    assert portfolio == ("https://example.dev")


def test_enrich_identity_with_links():
    identity = CandidateIdentity(
        full_name="Example User",
        email="example@example.com",
    )

    enriched = enrich_identity_with_pdf_links(
        identity,
        [
            ("https://www.linkedin.com/in/example-profile/"),
            ("https://github.com/example-user"),
        ],
    )

    assert enriched.linkedin_url == ("https://www.linkedin.com/in/example-profile/")

    assert enriched.github_url == ("https://github.com/example-user")


def test_existing_identity_links_are_preserved():
    identity = CandidateIdentity(
        linkedin_url=("https://www.linkedin.com/in/already-set/"),
    )

    enriched = enrich_identity_with_pdf_links(
        identity,
        ["https://www.linkedin.com/in/pdf-value/"],
    )

    assert enriched.linkedin_url == ("https://www.linkedin.com/in/already-set/")
