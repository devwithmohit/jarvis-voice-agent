from playwright.async_api import async_playwright, Browser, Page, Playwright
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import yaml
import logging

logger = logging.getLogger(__name__)


class BrowserExecutor:
    """Playwright-based browser automation"""

    def __init__(self, config_path: str = "config/browser.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        logger.info("BrowserExecutor initialized")

    async def initialize(self):
        """Start browser instance"""
        logger.info("Starting Playwright browser...")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config["browser"]["headless"]
        )

        self.page = await self.browser.new_page(
            viewport=self.config["browser"]["viewport"],
            user_agent=self.config["browser"]["user_agent"],
        )

        logger.info("Browser started successfully")

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL

        Args:
            url: URL to navigate to

        Returns:
            Dictionary with navigation result
        """
        logger.info(f"Navigating to: {url}")

        # Validate URL
        if not self._is_url_allowed(url):
            logger.warning(f"URL not allowed: {url}")
            return {"success": False, "error": f"URL domain not in allowed list: {url}"}

        try:
            response = await self.page.goto(
                url,
                timeout=self.config["browser"]["timeout_ms"],
                wait_until="networkidle",
            )

            title = await self.page.title()
            final_url = self.page.url

            logger.info(f"Navigation successful: {title}")

            return {
                "success": True,
                "url": final_url,
                "title": title,
                "status_code": response.status if response else 0,
            }

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return {"success": False, "error": str(e)}

    async def click_element(self, selector: str) -> Dict[str, Any]:
        """Click element by CSS selector

        Args:
            selector: CSS selector

        Returns:
            Dictionary with click result
        """
        logger.info(f"Clicking element: {selector}")

        try:
            await self.page.click(selector, timeout=5000)
            logger.info("Click successful")
            return {"success": True}

        except Exception as e:
            logger.error(f"Click failed: {e}")
            return {"success": False, "error": f"Failed to click element: {e}"}

    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into element

        Args:
            selector: CSS selector
            text: Text to type

        Returns:
            Dictionary with result
        """
        logger.info(f"Typing into element: {selector}")

        try:
            await self.page.fill(selector, text)
            logger.info("Type successful")
            return {"success": True}

        except Exception as e:
            logger.error(f"Type failed: {e}")
            return {"success": False, "error": f"Failed to type text: {e}"}

    async def get_text(self, selector: str) -> str:
        """Extract text from element

        Args:
            selector: CSS selector

        Returns:
            Extracted text or empty string
        """
        logger.info(f"Getting text from: {selector}")

        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.inner_text()
                logger.info(f"Extracted {len(text)} characters")
                return text

            logger.warning(f"Element not found: {selector}")
            return ""

        except Exception as e:
            logger.error(f"Get text failed: {e}")
            return f"Error: {e}"

    async def get_page_content(self) -> str:
        """Get full page HTML content

        Returns:
            Page HTML
        """
        logger.info("Getting page content")

        try:
            content = await self.page.content()
            logger.info(f"Retrieved {len(content)} characters")
            return content

        except Exception as e:
            logger.error(f"Get content failed: {e}")
            return ""

    async def screenshot(self, path: str) -> bool:
        """Take screenshot

        Args:
            path: Output file path

        Returns:
            True if successful
        """
        logger.info(f"Taking screenshot: {path}")

        try:
            await self.page.screenshot(path=path, full_page=True)
            logger.info("Screenshot saved")
            return True

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False

    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> bool:
        """Wait for element to appear

        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds

        Returns:
            True if element appeared
        """
        logger.info(f"Waiting for selector: {selector}")

        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            logger.info("Element appeared")
            return True

        except Exception as e:
            logger.warning(f"Wait timeout: {e}")
            return False

    def _is_url_allowed(self, url: str) -> bool:
        """Check if URL is in allowed list

        Args:
            url: URL to check

        Returns:
            True if allowed
        """
        try:
            domain = urlparse(url).netloc

            # Check blocked domains
            for blocked in self.config["security"]["blocked_domains"]:
                blocked_pattern = blocked.replace("*", "")
                if blocked_pattern in domain:
                    return False

            # Check allowed domains
            allowed_domains = self.config["security"]["allowed_domains"]
            return any(allowed in domain for allowed in allowed_domains)

        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

    async def close(self):
        """Cleanup resources"""
        logger.info("Closing browser...")

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        logger.info("Browser closed")
