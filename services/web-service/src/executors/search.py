from typing import List, Dict, Any
from playwright.async_api import Page
import yaml
import logging

logger = logging.getLogger(__name__)


class SearchExecutor:
    """Web search executor using Playwright"""

    def __init__(self, browser_page: Page, config_path: str = "config/browser.yaml"):
        self.page = browser_page

        with open(config_path) as f:
            config = yaml.safe_load(f)
            self.config = config["search"]

        logger.info("SearchExecutor initialized")

    async def search(
        self, query: str, engine: str = "google", max_results: int = 5
    ) -> List[Dict[str, str]]:
        """Perform web search and return results

        Args:
            query: Search query
            engine: Search engine name (google, bing)
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query} (engine: {engine})")

        engine_config = self.config["engines"].get(engine)
        if not engine_config:
            logger.error(f"Unknown search engine: {engine}")
            return []

        search_url = engine_config["url"].format(query=query)
        logger.info(f"Search URL: {search_url}")

        try:
            await self.page.goto(search_url, wait_until="networkidle")

            # Extract search results
            results = []
            result_elements = await self.page.query_selector_all(
                engine_config["result_selector"]
            )

            logger.info(f"Found {len(result_elements)} result elements")

            for i, element in enumerate(result_elements[:max_results]):
                try:
                    # Extract title
                    title_elem = await element.query_selector(
                        engine_config["title_selector"]
                    )
                    title = await title_elem.inner_text() if title_elem else ""

                    # Extract URL
                    link_elem = await element.query_selector(
                        engine_config["link_selector"]
                    )
                    url = await link_elem.get_attribute("href") if link_elem else ""

                    # Extract snippet
                    snippet = await self._extract_snippet(
                        element, engine_config["snippet_selector"]
                    )

                    if title and url:
                        results.append(
                            {
                                "title": title.strip(),
                                "url": url,
                                "snippet": snippet.strip(),
                            }
                        )
                        logger.debug(f"Result {i + 1}: {title[:50]}...")

                except Exception as e:
                    logger.warning(f"Failed to extract result {i + 1}: {e}")
                    continue

            logger.info(f"Successfully extracted {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def _extract_snippet(self, element, selector: str) -> str:
        """Extract description snippet from result

        Args:
            element: Parent element
            selector: CSS selector for snippet

        Returns:
            Snippet text or empty string
        """
        try:
            # Try multiple selectors (comma-separated)
            selectors = [s.strip() for s in selector.split(",")]

            for sel in selectors:
                snippet_elem = await element.query_selector(sel)
                if snippet_elem:
                    return await snippet_elem.inner_text()

            return ""

        except Exception as e:
            logger.debug(f"Snippet extraction failed: {e}")
            return ""
