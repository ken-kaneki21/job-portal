from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

from jobintel.company_discovery import detect_ats

MAX_LINKS = 300


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs,
    ) -> None:
        if tag.lower() != "a":
            return

        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)

                if len(self.links) >= MAX_LINKS:
                    return


def inspect_url_for_ats(
    url: str,
) -> tuple[str, str, str] | None:
    """
    Returns:

        (ats, identifier, career_url)

    Detection order:

    1. Original URL
    2. Redirect destination
    3. Links found on destination page
    """

    if not url:
        return None

    # ---------------------------------------------
    # 1. Direct URL detection
    # ---------------------------------------------

    direct = detect_ats(url)

    if direct is not None:
        ats, identifier = direct

        return (
            ats,
            identifier,
            url,
        )

    # ---------------------------------------------
    # 2. Follow redirects
    # ---------------------------------------------

    try:
        with httpx.Client(
            timeout=12.0,
            follow_redirects=True,
            headers={"User-Agent": ("Mozilla/5.0 (compatible; JobIntel/1.0)")},
        ) as client:
            response = client.get(url)

    except httpx.HTTPError:
        return None

    final_url = str(response.url)

    redirected = detect_ats(final_url)

    if redirected is not None:
        ats, identifier = redirected

        return (
            ats,
            identifier,
            final_url,
        )

    # ---------------------------------------------
    # 3. Inspect page links
    # ---------------------------------------------

    content_type = response.headers.get(
        "content-type",
        "",
    ).lower()

    if response.status_code != 200 or "text/html" not in content_type:
        return None

    parser = LinkParser()

    try:
        parser.feed(response.text)
    except Exception:
        return None

    for href in parser.links:
        absolute_url = urljoin(
            final_url,
            href,
        )

        detected = detect_ats(absolute_url)

        if detected is None:
            continue

        ats, identifier = detected

        return (
            ats,
            identifier,
            absolute_url,
        )

    return None


def inspect_urls_for_ats(
    urls: list[str],
) -> tuple[str, str, str] | None:
    seen = set()

    for url in urls:
        if not url:
            continue

        url = url.strip()

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        result = inspect_url_for_ats(url)

        if result is not None:
            return result

    return None
