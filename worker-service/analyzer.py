import os
import ssl
import time
import logging
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from s3_upload import upload_screenshot

logger = logging.getLogger(__name__)

# Known bad domains for demo purposes
KNOWN_BAD_DOMAINS = {
    "malware-test.example.com",
    "phishing-demo.example.com",
    "suspicious-site.example.net",
    "bad-actor.example.org",
    "exploit-kit.example.com",
    "ransomware-demo.example.net",
    "credential-stealer.example.com",
    "drive-by-download.example.org",
    "clickjack-demo.example.com",
    "seo-spam.example.net",
}

# Tech stack detection patterns
TECH_PATTERNS = {
    "WordPress": ["wp-content", "wp-includes", "wp-json"],
    "Next.js": ["__next", "_next/static", "__NEXT_DATA__"],
    "Nuxt.js": ["_nuxt", "__nuxt"],
    "React": ["react-root", "_reactRootContainer", "data-reactroot"],
    "Vue.js": ["data-v-", "__vue__"],
    "Angular": ["ng-version", "ng-app"],
    "Shopify": ["shopify", "cdn.shopify.com"],
    "Wix": ["wix.com", "parastorage.com"],
    "Django": ["csrfmiddlewaretoken"],
    "Laravel": ["laravel_session"],
    "jQuery": ["jquery.min.js", "jquery.js"],
    "Bootstrap": ["bootstrap.min.css", "bootstrap.min.js"],
    "Tailwind CSS": ["tailwindcss"],
}


async def analyze_url(url: str) -> dict:
    """
    Perform a comprehensive analysis of a given URL.
    Returns a dictionary with all analysis fields.
    """
    result = {
        "url": url,
        "title": None,
        "description": None,
        "status_code": None,
        "response_time_ms": None,
        "redirect_chain": [],
        "ssl_valid": None,
        "ssl_expires_at": None,
        "tech_stack": [],
        "safety_score": "safe",
        "screenshot_url": None,
        "analyzed_at": datetime.utcnow().isoformat(),
    }

    parsed = urlparse(url)
    domain = parsed.hostname or ""

    # Safety check - known bad domains
    if domain in KNOWN_BAD_DOMAINS:
        result["safety_score"] = "dangerous"
    elif not url.startswith("https://"):
        result["safety_score"] = "suspicious"

    # Fetch the URL
    try:
        start = time.monotonic()
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            verify=True,
        ) as client:
            response = await client.get(url)

        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        result["status_code"] = response.status_code
        result["response_time_ms"] = elapsed_ms
        result["ssl_valid"] = url.startswith("https://")

        # Record redirect chain
        if response.history:
            result["redirect_chain"] = [str(r.url) for r in response.history]

        # Parse HTML
        html = response.text
        soup = BeautifulSoup(html, "lxml")

        # Title
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            result["title"] = title_tag.string.strip()[:200]

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            result["description"] = meta_desc["content"].strip()[:500]

        # Tech stack detection from headers
        server = response.headers.get("server", "")
        if server:
            result["tech_stack"].append(f"Server: {server}")

        powered_by = response.headers.get("x-powered-by", "")
        if powered_by:
            result["tech_stack"].append(f"X-Powered-By: {powered_by}")

        x_generator = response.headers.get("x-generator", "")
        if x_generator:
            result["tech_stack"].append(f"X-Generator: {x_generator}")

        # Tech stack detection from HTML
        for tech, patterns in TECH_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in html.lower():
                    if tech not in result["tech_stack"]:
                        result["tech_stack"].append(tech)
                    break

    except httpx.ConnectError as e:
        logger.error(f"Connection error for {url}: {e}")
        result["safety_score"] = "suspicious"
        result["ssl_valid"] = False
        return result
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        if result["ssl_valid"] is None and url.startswith("https://"):
             result["ssl_valid"] = False
        return result

    # SSL certificate check
    if url.startswith("https://"):
        try:
            ctx = ssl.create_default_context()
            conn = ctx.wrap_socket(
                __import__("socket").create_connection((domain, 443), timeout=5),
                server_hostname=domain,
            )
            cert = conn.getpeercert()
            conn.close()
            if cert:
                result["ssl_valid"] = True
                not_after = cert.get("notAfter", "")
                if not_after:
                    result["ssl_expires_at"] = not_after
        except ssl.SSLError:
            result["ssl_valid"] = False
            if result["safety_score"] == "safe":
                result["safety_score"] = "suspicious"
        except Exception as e:
            logger.warning(f"SSL check error for {domain}: {e}")

    # Screenshot with Playwright
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            page = await browser.new_page(viewport={"width": 1280, "height": 720})
            await page.goto(url, timeout=15000, wait_until="networkidle")
            screenshot_bytes = await page.screenshot(type="png")
            await browser.close()

            # Upload to S3 (or save locally)
            filename = f"{domain}_{int(time.time())}.png"
            screenshot_url = await upload_screenshot(screenshot_bytes, filename)
            result["screenshot_url"] = screenshot_url

    except Exception as e:
        logger.warning(f"Screenshot failed for {url}: {e}")
        result["screenshot_url"] = None

    return result
