"""Read-only retrieval of allowlisted public NIAT pages."""

from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


APPROVED_SOURCES = {
    "niat_overview": "https://www.niatindia.com/",
    "niat_knowledge": "https://www.niatindia.com/llm-info",
    "niat_application": (
        "https://apply.niatindia.com/login-upskill"
    ),
}

MAX_BYTES = 1_000_000
MAX_TEXT_CHARS = 18_000


def _approved_url(url):
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.hostname in {
            "www.niatindia.com",
            "apply.niatindia.com",
        }
        and parsed.username is None
        and parsed.password is None
    )


class PublicPageParser(HTMLParser):
    SKIPPED_TAGS = {
        "script", "style", "noscript", "svg",
    }

    def __init__(self):
        super().__init__()
        self.title = []
        self.content = []
        self._in_title = False
        self._skip_stack = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIPPED_TAGS:
            self._skip_stack.append(tag)
            return

        if self._skip_stack:
            return

        if tag == "title":
            self._in_title = True

        if tag in (
            "p", "h1", "h2", "h3", "h4",
            "li", "section", "article",
        ):
            self.content.append("\n")

    def handle_endtag(self, tag):
        if self._skip_stack:
            if tag == self._skip_stack[-1]:
                self._skip_stack.pop()
            return

        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._skip_stack:
            return

        if self._in_title:
            self.title.append(data)

        value = " ".join(data.split())
        if value:
            self.content.append(value)


def fetch_public_source(source_id):
    """Retrieve one allowlisted public page with metadata."""
    if source_id not in APPROVED_SOURCES:
        raise ValueError("Source is not approved")

    url = APPROVED_SOURCES[source_id]

    if not _approved_url(url):
        raise ValueError("Source URL is not approved")

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "NIATParentDecisionBrief/1.0"
            )
        },
    )

    try:
        with urlopen(request, timeout=12) as response:
            final_url = response.geturl()

            if not _approved_url(final_url):
                raise ValueError(
                    "Redirected to an unapproved URL"
                )

            content_type = response.headers.get(
                "Content-Type", ""
            )

            if "text/html" not in content_type.lower():
                raise ValueError(
                    "Expected a public HTML page"
                )

            raw = response.read(MAX_BYTES + 1)
            html_truncated = len(raw) > MAX_BYTES

            if html_truncated:
                raw = raw[:MAX_BYTES]

            status = response.status

    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"Public source retrieval failed: {source_id}"
        ) from exc

    parser = PublicPageParser()
    parser.feed(
        raw.decode("utf-8", errors="replace")
    )

    text = " ".join(
        " ".join(parser.content).split()
    )

    return {
        "source_id": source_id,
        "url": final_url,
        "title": " ".join(parser.title).strip(),
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "http_status": status,
        "content": text[:MAX_TEXT_CHARS],
        "truncated": (
            html_truncated
            or len(text) > MAX_TEXT_CHARS
        ),
        "html_truncated": html_truncated,
    }


def retrieve_public_knowledge():
    """Retrieve the two primary informational sources."""
    results = []
    errors = []

    for source_id in (
        "niat_knowledge",
        "niat_overview",
    ):
        try:
            results.append(
                fetch_public_source(source_id)
            )
        except (RuntimeError, ValueError) as exc:
            errors.append({
                "source_id": source_id,
                "error": str(exc),
            })

    return {
        "sources": results,
        "errors": errors,
    }
