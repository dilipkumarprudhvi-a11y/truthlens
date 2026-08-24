"""
Secure Server-Side URL Extraction Service with SSRF Protection
Safely fetches and parses web articles while blocking internal network exploitation.
"""

import ipaddress
import socket
import urllib.parse
from typing import Optional
import httpx
from bs4 import BeautifulSoup

from ..schemas.analysis import UrlExtractResponse

MAX_URL_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB max response
URL_FETCH_TIMEOUT = 5.0  # 5 seconds max


def is_safe_url(target_url: str) -> bool:
    """
    SSRF Guard: Validates that the URL uses HTTP/HTTPS and resolves
    only to safe public routable IP addresses.
    """
    try:
        parsed = urllib.parse.urlparse(target_url)
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Block localhost and common internal names
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
            return False

        # Resolve hostname to IP addresses
        addr_info = socket.getaddrinfo(hostname, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            ip_obj = ipaddress.ip_address(ip_str)

            # Block private, loopback, link-local, multicast, or reserved ranges
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            ):
                return False

        return True
    except Exception:
        return False


async def extract_url_content(target_url: str) -> UrlExtractResponse:
    """
    Securely fetches article HTML and extracts title, author, date, and clean body text.
    """
    if not is_safe_url(target_url):
        return UrlExtractResponse(
            url=target_url,
            text="",
            length=0,
            success=False,
            error="Security Error: Target URL is invalid or points to an inaccessible/private network address."
        )

    headers = {
        "User-Agent": "TruthLens-ArticleExtractor/3.0 (+https://truthlens.ai/bot)",
        "Accept": "text/html,application/xhtml+xml"
    }

    try:
        async with httpx.AsyncClient(timeout=URL_FETCH_TIMEOUT, follow_redirects=True, max_redirects=3) as client:
            res = await client.get(target_url, headers=headers)

            if res.status_code != 200:
                return UrlExtractResponse(
                    url=target_url,
                    text="",
                    length=0,
                    success=False,
                    error=f"Server returned HTTP status code {res.status_code}."
                )

            # Validate Content-Type
            content_type = res.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return UrlExtractResponse(
                    url=target_url,
                    text="",
                    length=0,
                    success=False,
                    error=f"Unsupported content type '{content_type}'. TruthLens extracts HTML web articles only."
                )

            html = res.text[:MAX_URL_RESPONSE_BYTES]

    except httpx.TimeoutException:
        return UrlExtractResponse(
            url=target_url,
            text="",
            length=0,
            success=False,
            error="Request timed out while connecting to the target server."
        )
    except Exception as e:
        return UrlExtractResponse(
            url=target_url,
            text="",
            length=0,
            success=False,
            error=f"Failed to fetch URL: {str(e)}"
        )

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer, ads
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form", "svg"]):
        tag.decompose()

    # Extract Title
    title = None
    if soup.find("meta", property="og:title"):
        title = soup.find("meta", property="og:title").get("content")
    elif soup.find("title"):
        title = soup.find("title").get_text()
    elif soup.find("h1"):
        title = soup.find("h1").get_text()

    # Extract Author
    author = None
    if soup.find("meta", attrs={"name": "author"}):
        author = soup.find("meta", attrs={"name": "author"}).get("content")
    elif soup.find("meta", property="article:author"):
        author = soup.find("meta", property="article:author").get("content")

    # Extract Date
    publish_date = None
    if soup.find("meta", property="article:published_time"):
        publish_date = soup.find("meta", property="article:published_time").get("content")
    elif soup.find("time"):
        publish_date = soup.find("time").get_text()

    # Extract Body Content
    article_container = soup.find("article") or soup.find("main") or soup.body
    paragraphs = article_container.find_all("p") if article_container else []
    extracted_paragraphs = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30]

    body_text = "\n\n".join(extracted_paragraphs)
    if not body_text and article_container:
        body_text = article_container.get_text(separator="\n", strip=True)

    if not body_text or len(body_text.strip()) < 40:
        return UrlExtractResponse(
            url=target_url,
            title=title.strip() if title else None,
            author=author.strip() if author else None,
            publish_date=publish_date.strip() if publish_date else None,
            text="",
            length=0,
            success=False,
            error="Could not extract substantial article text. The page may require JavaScript or authentication."
        )

    clean_text = body_text.strip()
    return UrlExtractResponse(
        url=target_url,
        title=title.strip() if title else None,
        author=author.strip() if author else None,
        publish_date=publish_date.strip() if publish_date else None,
        text=clean_text,
        length=len(clean_text.split()),
        success=True
    )
