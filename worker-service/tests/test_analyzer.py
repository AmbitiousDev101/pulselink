"""Tests for PulseLink worker-service URL analyzer."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def mock_s3():
    with patch(
        "s3_upload.upload_screenshot",
        new_callable=AsyncMock,
        return_value="https://bucket.s3.amazonaws.com/screenshots/test.png",
    ):
        yield


@pytest.fixture
def anyio_backend():
    return "asyncio"


def make_playwright_mock():
    mock_page = AsyncMock()
    mock_page.screenshot = AsyncMock(return_value=b"fake-png-data")
    mock_page.goto = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()

    mock_p = AsyncMock()
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_p)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_async_playwright = MagicMock(return_value=mock_ctx)
    return mock_async_playwright


@pytest.mark.anyio
async def test_analyze_known_safe_url():
    with patch("httpx.AsyncClient") as MockClient, \
         patch("playwright.async_api.async_playwright", make_playwright_mock()):

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head>
            <title>Example Domain</title>
            <meta name="description" content="This is an example website.">
        </head>
        <body><h1>Example</h1></body>
        </html>
        """
        mock_response.headers = {"server": "nginx", "content-type": "text/html"}
        mock_response.history = []

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client_instance

        from analyzer import analyze_url
        result = await analyze_url("https://example.com")

        assert result["url"] == "https://example.com"
        assert "title" in result
        assert "status_code" in result
        assert "response_time_ms" in result
        assert "redirect_chain" in result
        assert isinstance(result["redirect_chain"], list)
        assert "ssl_valid" in result
        assert "tech_stack" in result
        assert "safety_score" in result
        assert result["safety_score"] in ("safe", "suspicious", "dangerous")
        assert "screenshot_url" in result
        assert "analyzed_at" in result


@pytest.mark.anyio
async def test_analyze_suspicious_url():
    with patch("httpx.AsyncClient") as MockClient, \
         patch("playwright.async_api.async_playwright", make_playwright_mock()):

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<html><head><title>Test</title></head><body></body></html>"
        mock_response.headers = {}
        mock_response.history = []

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client_instance

        from analyzer import analyze_url
        result = await analyze_url("http://example.com")
        assert result["safety_score"] == "suspicious"


@pytest.mark.anyio
async def test_analyze_returns_tech_stack():
    with patch("httpx.AsyncClient") as MockClient, \
         patch("playwright.async_api.async_playwright", make_playwright_mock()):

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head><title>WordPress Site</title></head>
        <body>
            <link rel="stylesheet" href="/wp-content/themes/theme/style.css">
        </body>
        </html>
        """
        mock_response.headers = {"server": "Apache", "x-powered-by": "PHP/8.1"}
        mock_response.history = []

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client_instance

        from analyzer import analyze_url
        result = await analyze_url("https://wordpress-site.example.com")
        assert "Server: Apache" in result["tech_stack"]
        assert "X-Powered-By: PHP/8.1" in result["tech_stack"]
        assert "WordPress" in result["tech_stack"]
