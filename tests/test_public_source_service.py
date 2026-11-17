import pytest

from app.services.public_source_service import (
    PublicPageParser,
    _approved_url,
    fetch_public_source,
)


def test_approved_official_urls():
    assert _approved_url(
        "https://www.niatindia.com/llm-info"
    )
    assert _approved_url(
        "https://apply.niatindia.com/login-upskill"
    )


def test_unapproved_urls_rejected():
    assert not _approved_url(
        "http://www.niatindia.com/"
    )
    assert not _approved_url(
        "https://niatindia.com.evil.example/"
    )
    assert not _approved_url(
        "https://example.com/"
    )


def test_unknown_source_rejected():
    with pytest.raises(ValueError):
        fetch_public_source("unapproved_source")


def test_html_parser_extracts_readable_text():
    parser = PublicPageParser()

    parser.feed("""
        <html>
          <head>
            <title>Official NIAT Page</title>
            <style>.hidden {display:none}</style>
          </head>
          <body>
            <h1>NIAT Upskilling</h1>
            <p>Program information</p>
            <script>secret_internal_code()</script>
          </body>
        </html>
    """)

    content = " ".join(parser.content)

    assert "NIAT Upskilling" in content
    assert "Program information" in content
    assert "secret_internal_code" not in content
    assert "Official NIAT Page" in "".join(parser.title)


def test_nested_skipped_content():
    parser = PublicPageParser()

    parser.feed("""
        <div>Before</div>
        <svg>
          <g>
            <text>Hidden SVG Text</text>
          </g>
        </svg>
        <p>After</p>
    """)

    content = " ".join(parser.content)

    assert "Before" in content
    assert "After" in content
    assert "Hidden SVG Text" not in content


def test_large_html_page_returns_bounded_content(
    monkeypatch,
):
    from app.services import public_source_service as service

    class FakeResponse:
        status = 200
        headers = {
            "Content-Type": "text/html; charset=utf-8"
        }

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def geturl(self):
            return service.APPROVED_SOURCES[
                "niat_overview"
            ]

        def read(self, size):
            return (
                b"<html><title>NIAT</title>"
                b"<body><p>Public program overview</p>"
                + b" " * size
            )

    monkeypatch.setattr(
        service,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )

    result = service.fetch_public_source(
        "niat_overview"
    )

    assert result["http_status"] == 200
    assert result["html_truncated"] is True
    assert result["truncated"] is True
    assert "Public program overview" in result["content"]
