"""
gRPC Clients for inter-service communication
Provides clients for memory-service, tool-executor, and web-service
"""

import grpc
from typing import Optional, Dict, Any, List
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from config import get_settings

settings = get_settings()


class MemoryServiceClient:
    """
    Client for memory-service gRPC API
    Handles user memory storage and retrieval
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """Initialize memory service client"""
        self.host = host or settings.memory_service_host
        self.port = port or settings.memory_service_port
        self.address = f"{self.host}:{self.port}"
        self.channel = None
        self.stub = None

    def connect(self):
        """Establish connection to memory service"""
        try:
            self.channel = grpc.insecure_channel(self.address)
            # Import proto-generated stub here to avoid circular imports
            # from generated.memory_pb2_grpc import MemoryServiceStub
            # self.stub = MemoryServiceStub(self.channel)
            print(f"Connected to memory-service at {self.address}")
        except Exception as e:
            print(f"Failed to connect to memory-service: {e}")
            raise

    def close(self):
        """Close connection"""
        if self.channel:
            self.channel.close()

    def store_memory(
        self, user_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store memory for user

        Args:
            user_id: User identifier
            content: Memory content
            metadata: Optional metadata

        Returns:
            Response with memory_id
        """
        if not self.stub:
            self.connect()

        try:
            # Placeholder - replace with actual proto call
            # request = StoreMemoryRequest(
            #     user_id=user_id,
            #     content=content,
            #     metadata=metadata or {}
            # )
            # response = self.stub.StoreMemory(request)
            # return {"memory_id": response.memory_id, "success": True}

            return {"memory_id": "mock_memory_id", "success": True}
        except Exception as e:
            print(f"Error storing memory: {e}")
            return {"success": False, "error": str(e)}

    def search_memories(
        self, user_id: str, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search user memories

        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum results

        Returns:
            List of matching memories
        """
        if not self.stub:
            self.connect()

        try:
            # Placeholder - replace with actual proto call
            # request = SearchMemoriesRequest(
            #     user_id=user_id,
            #     query=query,
            #     limit=limit
            # )
            # response = self.stub.SearchMemories(request)
            # return [
            #     {
            #         "memory_id": m.memory_id,
            #         "content": m.content,
            #         "relevance": m.relevance_score,
            #         "metadata": dict(m.metadata)
            #     }
            #     for m in response.memories
            # ]

            return []
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []


class ToolExecutorClient:
    """
    Client for tool-executor gRPC API
    Handles file and system command execution
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """Initialize tool executor client"""
        self.host = host or settings.tool_executor_host
        self.port = port or settings.tool_executor_port
        self.address = f"{self.host}:{self.port}"
        self.channel = None
        self.stub = None

    def connect(self):
        """Establish connection to tool executor"""
        try:
            self.channel = grpc.insecure_channel(self.address)
            # from generated.tool_executor_pb2_grpc import ToolExecutorStub
            # self.stub = ToolExecutorStub(self.channel)
            print(f"Connected to tool-executor at {self.address}")
        except Exception as e:
            print(f"Failed to connect to tool-executor: {e}")
            raise

    def close(self):
        """Close connection"""
        if self.channel:
            self.channel.close()

    def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute tool action

        Args:
            tool_name: Tool name (file_read, file_write, system_command, etc.)
            parameters: Tool parameters

        Returns:
            Execution result
        """
        if not self.stub:
            self.connect()

        try:
            # Placeholder - replace with actual proto call
            # request = ExecuteToolRequest(
            #     tool_name=tool_name,
            #     parameters=parameters
            # )
            # response = self.stub.ExecuteTool(request)
            # return {
            #     "success": response.success,
            #     "result": response.result,
            #     "error": response.error if not response.success else None
            # }

            return {
                "success": True,
                "result": f"Mock execution of {tool_name}",
                "error": None,
            }
        except Exception as e:
            print(f"Error executing tool {tool_name}: {e}")
            return {"success": False, "result": None, "error": str(e)}


class WebServiceClient:
    """
    Client for web-service gRPC API
    Handles web search, fetch, and browser automation
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """Initialize web service client"""
        self.host = host or settings.web_service_host
        self.port = port or settings.web_service_port
        self.address = f"{self.host}:{self.port}"
        self.channel = None
        self.stub = None

    def connect(self):
        """Establish connection to web service"""
        try:
            self.channel = grpc.insecure_channel(self.address)
            # from generated.web_service_pb2_grpc import WebServiceStub
            # self.stub = WebServiceStub(self.channel)
            print(f"Connected to web-service at {self.address}")
        except Exception as e:
            print(f"Failed to connect to web-service: {e}")
            raise

    def close(self):
        """Close connection"""
        if self.channel:
            self.channel.close()

    def web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Perform web search

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            Search results
        """
        if not self.stub:
            self.connect()

        try:
            # Placeholder - replace with actual proto call
            # request = WebSearchRequest(
            #     query=query,
            #     max_results=max_results
            # )
            # response = self.stub.WebSearch(request)
            # return {
            #     "success": True,
            #     "results": [
            #         {
            #             "title": r.title,
            #             "url": r.url,
            #             "snippet": r.snippet
            #         }
            #         for r in response.results
            #     ]
            # }

            return {
                "success": True,
                "results": [
                    {
                        "title": f"Result for {query}",
                        "url": "https://example.com",
                        "snippet": "Mock search result",
                    }
                ],
            }
        except Exception as e:
            print(f"Error performing web search: {e}")
            return {"success": False, "results": [], "error": str(e)}

    def web_fetch(self, url: str, extract_type: str = "text") -> Dict[str, Any]:
        """
        Fetch web page content

        Args:
            url: URL to fetch
            extract_type: Content type (text, markdown, html)

        Returns:
            Fetched content
        """
        if not self.stub:
            self.connect()

        try:
            # Placeholder - replace with actual proto call
            # request = WebFetchRequest(
            #     url=url,
            #     extract_type=extract_type
            # )
            # response = self.stub.WebFetch(request)
            # return {
            #     "success": True,
            #     "content": response.content,
            #     "title": response.title
            # }

            return {
                "success": True,
                "content": f"Mock content from {url}",
                "title": "Mock Page",
            }
        except Exception as e:
            print(f"Error fetching web page: {e}")
            return {"success": False, "content": None, "error": str(e)}

    def browser_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute browser action

        Args:
            action: Action name (navigate, click, type)
            parameters: Action parameters

        Returns:
            Action result
        """
        if not self.stub:
            self.connect()

        try:
            # Placeholder - replace with actual proto call
            # request = BrowserActionRequest(
            #     action=action,
            #     parameters=parameters
            # )
            # response = self.stub.BrowserAction(request)
            # return {
            #     "success": response.success,
            #     "result": response.result,
            #     "error": response.error if not response.success else None
            # }

            return {
                "success": True,
                "result": f"Mock browser action: {action}",
                "error": None,
            }
        except Exception as e:
            print(f"Error executing browser action: {e}")
            return {"success": False, "result": None, "error": str(e)}


class GrpcClientManager:
    """
    Manages all gRPC client connections
    Provides centralized access to service clients
    """

    def __init__(self):
        """Initialize client manager"""
        self.memory_client = MemoryServiceClient()
        self.tool_executor_client = ToolExecutorClient()
        self.web_client = WebServiceClient()
        self._connected = False

    def connect_all(self):
        """Connect to all services"""
        try:
            self.memory_client.connect()
            self.tool_executor_client.connect()
            self.web_client.connect()
            self._connected = True
            print("All gRPC clients connected successfully")
        except Exception as e:
            print(f"Error connecting gRPC clients: {e}")
            raise

    def close_all(self):
        """Close all connections"""
        self.memory_client.close()
        self.tool_executor_client.close()
        self.web_client.close()
        self._connected = False
        print("All gRPC clients closed")

    def is_connected(self) -> bool:
        """Check if clients are connected"""
        return self._connected

    def __enter__(self):
        """Context manager entry"""
        self.connect_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_all()
