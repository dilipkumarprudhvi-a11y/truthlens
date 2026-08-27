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

MAX_URL_RESPONSE_BYTES = 3 * 1024 * 1024  # 3MB max response
URL_FETCH_TIMEOUT = 10.0  # 10 seconds max

# ... (is_safe_url logic unchanged) ...



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
    Uses multi-agent fallback for Wikipedia and anti-bot protected news sites.
    """
    if not is_safe_url(target_url):
        return UrlExtractResponse(
            url=target_url,
            text="",
            length=0,
            success=False,
            error="Security Error: Target URL is invalid or points to an inaccessible/private network address."
        )

    # Multi-agent header configurations
    is_wiki = "wikipedia.org" in target_url.lower() or "wikimedia.org" in target_url.lower()
    
    agent_options = [
        # Dedicated Research Bot Agent (Required by Wikipedia & open knowledge repositories)
        {
            "User-Agent": "TruthLens/3.0 (https://dilipkumarprudhvi-a11y.github.io/truthlens/; contact@truthlens.ai)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        },
        # Standard Modern Browser Agent (For general news publishers)
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
    ]

    if not is_wiki:
        # Prioritize standard browser agent for non-wiki sites
        agent_options.reverse()

    html = None
    last_status = None
    last_error = None

    async with httpx.AsyncClient(timeout=URL_FETCH_TIMEOUT, follow_redirects=True, max_redirects=4) as client:
        for headers in agent_options:
            try:
                res = await client.get(target_url, headers=headers)
                last_status = res.status_code
                if res.status_code == 200:
                    content_type = res.headers.get("Content-Type", "").lower()
                    if "text/html" in content_type or "application/xhtml" in content_type or "text/plain" in content_type:
                        html = res.text[:MAX_URL_RESPONSE_BYTES]
                        break
            except httpx.TimeoutException:
                last_error = "Request timed out while connecting to the target server."
            except Exception as e:
                last_error = f"Connection error: {str(e)}"

    if not html:
        return UrlExtractResponse(
            url=target_url,
            text="",
            length=0,
            success=False,
            error=last_error or f"Server returned HTTP status code {last_status or 'error'}."
        )

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer, ads, tables, sidebars
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form", "svg", "table"]):
        tag.decompose()

    # Extract Title
    title = None
    if soup.find("h1"):
        title = soup.find("h1").get_text()
    elif soup.find("meta", property="og:title"):
        title = soup.find("meta", property="og:title").get("content")
    elif soup.find("title"):
        title = soup.find("title").get_text()

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
    article_container = (
        soup.find("div", id="mw-content-text")
        or soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=lambda c: c and any(k in c.lower() for k in ["article", "content", "story", "post"]))
        or soup.body
    )
    paragraphs = article_container.find_all("p") if article_container else []
    extracted_paragraphs = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30]

    # Limit to first 20 paragraphs to prevent 10,000-word overloads on encyclopedias
    selected_paragraphs = extracted_paragraphs[:20]
    body_text = "\n\n".join(selected_paragraphs)
    
    if not body_text and article_container:
        body_text = article_container.get_text(separator="\n", strip=True)

    if not body_text or len(body_text.strip()) < 30:
        return UrlExtractResponse(
            url=target_url,
            title=title.strip() if title else None,
            author=author.strip() if author else None,
            publish_date=publish_date.strip() if publish_date else None,
            text="",
            length=0,
            success=False,
            error="Could not extract readable article text. The page may require JavaScript or authentication."
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
