import grpc
from concurrent import futures
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.executors.browser import BrowserExecutor
from src.executors.search import SearchExecutor
from src.executors.scraper import Scraper
from config import settings

# TODO: Import generated proto files after generation
# from generated import web_pb2, web_pb2_grpc

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WebServicer:
    """gRPC servicer for web automation"""

    def __init__(self):
        logger.info("Initializing Web servicer...")
        self.browser = BrowserExecutor()
        self.scraper = Scraper()
        self.search_executor = None

        # Initialize browser
        asyncio.run(self._async_init())

        logger.info("Web servicer initialized successfully")

    async def _async_init(self):
        """Async initialization"""
        await self.browser.initialize()
        self.search_executor = SearchExecutor(self.browser.page)

    def Navigate(self, request, context):
        """Navigate to URL

        Args:
            request: NavigateRequest
            context: gRPC context

        Returns:
            NavigateResponse
        """
        logger.info(f"Navigate request: {request.url}")

        result = asyncio.run(self.browser.navigate(request.url))

        # TODO: Return actual proto message
        # return web_pb2.NavigateResponse(
        #     success=result["success"],
        #     final_url=result.get("url", ""),
        #     title=result.get("title", ""),
        #     status_code=result.get("status_code", 0),
        #     error=result.get("error", "")
        # )

        logger.info(f"Navigate result: success={result['success']}")
        return result

    def Search(self, request, context):
        """Perform web search

        Args:
            request: SearchRequest
            context: gRPC context

        Returns:
            SearchResponse
        """
        logger.info(f"Search request: {request.query}")

        results = asyncio.run(
            self.search_executor.search(
                query=request.query,
                engine=request.engine or "google",
                max_results=request.max_results or 5,
            )
        )

        # TODO: Return actual proto message
        # search_results = [
        #     web_pb2.SearchResult(
        #         title=r["title"],
        #         url=r["url"],
        #         snippet=r["snippet"]
        #     )
        #     for r in results
        # ]
        #
        # return web_pb2.SearchResponse(
        #     results=search_results,
        #     total_count=len(results)
        # )

        logger.info(f"Search returned {len(results)} results")
        return {"results": results}

    def ClickElement(self, request, context):
        """Click element on page

        Args:
            request: ClickRequest
            context: gRPC context

        Returns:
            ActionResponse
        """
        logger.info(f"Click request: {request.selector}")

        result = asyncio.run(self.browser.click_element(request.selector))

        # TODO: Return actual proto message
        return result

    def ExtractText(self, request, context):
        """Extract text from current page

        Args:
            request: ExtractRequest
            context: gRPC context

        Returns:
            ExtractResponse
        """
        logger.info("Extract text request")

        html = asyncio.run(self.browser.get_page_content())

        if request.selector:
            # Extract by selector
            texts = self.scraper.extract_by_selector(html, request.selector)
            text = "\n".join(texts)
        else:
            # Extract all text
            text = self.scraper.extract_text(html)

        # TODO: Return actual proto message
        logger.info(f"Extracted {len(text)} characters")
        return {"text": text, "success": True}

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, "browser"):
            asyncio.run(self.browser.close())


def serve():
    """Start the gRPC server"""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ],
    )

    # TODO: Add servicer after proto generation
    # web_pb2_grpc.add_WebServiceServicer_to_server(WebServicer(), server)

    servicer = WebServicer()

    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    server.start()

    logger.info(
        f"Web Service gRPC server started on {settings.grpc_host}:{settings.grpc_port}"
    )
    logger.info(f"Browser headless: {settings.headless}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down Web Service...")
        server.stop(grace=5)


if __name__ == "__main__":
    serve()
