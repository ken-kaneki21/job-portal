import hashlib
import re


COMPANY_SUFFIXES = {
    "inc",
    "incorporated",
    "ltd",
    "limited",
    "llc",
    "pvt",
    "private",
    "corporation",
    "corp",
}


COMPANY_ALIASES = {
    "tata consultancy services": "tcs",
}


LOCATION_ALIASES = {
    "bengaluru": "bangalore",
}


def normalize_spaces(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def normalize_company(
    value: str,
) -> str:
    value = value.lower()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    value = normalize_spaces(value)

    tokens = [
        token
        for token in value.split()
        if token not in COMPANY_SUFFIXES
    ]

    value = " ".join(tokens)

    return COMPANY_ALIASES.get(
        value,
        value,
    )


def normalize_title(
    value: str,
) -> str:
    value = value.lower()

    # Keep words inside parentheses.
    # Parenthetical text often contains meaningful
    # differentiators such as East/West, location,
    # platform, team, product, etc.
    value = value.replace("(", " ")
    value = value.replace(")", " ")

    # Normalize common dash variants.
    value = value.replace("–", "-")
    value = value.replace("—", "-")

    value = re.sub(
        r"[^a-z0-9+#\s-]",
        " ",
        value,
    )

    value = normalize_spaces(value)

    return value


def normalize_location(
    value: str | None,
) -> str:
    if not value:
        return ""

    value = value.lower()

    value = value.replace("–", "-")
    value = value.replace("—", "-")

    for old, new in LOCATION_ALIASES.items():
        value = value.replace(
            old,
            new,
        )

    value = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        value,
    )

    value = normalize_spaces(value)

    return value


def canonical_key(
    *,
    company: str,
    title: str,
    location: str | None,
) -> str:
    """
    Candidate/blocking key used to find possible
    cross-source duplicates.

    IMPORTANT:
    This is NOT guaranteed to uniquely identify
    a real-world job requisition.
    """

    candidate = "|".join(
        [
            normalize_company(company),
            normalize_title(title),
            normalize_location(location),
        ]
    )

    return hashlib.sha256(
        candidate.encode("utf-8")
    ).hexdigest()