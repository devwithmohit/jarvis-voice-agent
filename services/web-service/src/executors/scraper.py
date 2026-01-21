from bs4 import BeautifulSoup
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class Scraper:
    """Web scraping utilities using BeautifulSoup"""

    def __init__(self):
        logger.info("Scraper initialized")

    def extract_text(self, html: str) -> str:
        """Extract all text from HTML

        Args:
            html: HTML content

        Returns:
            Extracted text
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)

            logger.info(f"Extracted {len(text)} characters of text")
            return text

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""

    def extract_links(self, html: str, base_url: str = "") -> List[Dict[str, str]]:
        """Extract all links from HTML

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of links with text and href
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            links = []

            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)

                # Resolve relative URLs if base_url provided
                if base_url and not href.startswith(("http://", "https://")):
                    from urllib.parse import urljoin

                    href = urljoin(base_url, href)

                links.append({"text": text, "href": href})

            logger.info(f"Extracted {len(links)} links")
            return links

        except Exception as e:
            logger.error(f"Link extraction failed: {e}")
            return []

    def extract_metadata(self, html: str) -> Dict[str, str]:
        """Extract page metadata (title, description, etc.)

        Args:
            html: HTML content

        Returns:
            Dictionary of metadata
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            metadata = {}

            # Title
            title = soup.find("title")
            if title:
                metadata["title"] = title.get_text(strip=True)

            # Meta description
            description = soup.find("meta", attrs={"name": "description"})
            if description and description.get("content"):
                metadata["description"] = description["content"]

            # Meta keywords
            keywords = soup.find("meta", attrs={"name": "keywords"})
            if keywords and keywords.get("content"):
                metadata["keywords"] = keywords["content"]

            # Open Graph tags
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                metadata["og_title"] = og_title["content"]

            og_description = soup.find("meta", property="og:description")
            if og_description and og_description.get("content"):
                metadata["og_description"] = og_description["content"]

            logger.info(f"Extracted {len(metadata)} metadata fields")
            return metadata

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {}

    def extract_by_selector(self, html: str, selector: str) -> List[str]:
        """Extract elements by CSS selector

        Args:
            html: HTML content
            selector: CSS selector

        Returns:
            List of extracted text
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            elements = soup.select(selector)

            texts = [elem.get_text(strip=True) for elem in elements]
            logger.info(f"Extracted {len(texts)} elements with selector: {selector}")

            return texts

        except Exception as e:
            logger.error(f"Selector extraction failed: {e}")
            return []
