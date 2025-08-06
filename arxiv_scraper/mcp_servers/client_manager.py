"""
MCP Client Manager for coordinating communication with external MCP servers.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class ServerStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPServerConfig:
    name: str
    host: str = "localhost"
    port: int = 3000
    protocol: str = "http"
    timeout: int = 30
    retry_attempts: int = 3
    tools: List[str] = field(default_factory=list)


class MCPClient(ABC):
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.status = ServerStatus.DISCONNECTED
        self.logger = logging.getLogger(f"mcp.{config.name}")
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass


class HTTPMCPClient(MCPClient):
    def __init__(self, config: MCPServerConfig):
        super().__init__(config)
        self.session = None
    
    async def connect(self) -> bool:
        import aiohttp
        try:
            self.status = ServerStatus.CONNECTING
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
            # Test connection with health check
            if await self.health_check():
                self.status = ServerStatus.CONNECTED
                self.logger.info(f"Connected to {self.config.name}")
                return True
            else:
                self.status = ServerStatus.ERROR
                return False
                
        except Exception as e:
            self.logger.error(f"Connection failed to {self.config.name}: {e}")
            self.status = ServerStatus.ERROR
            return False
    
    async def disconnect(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None
        self.status = ServerStatus.DISCONNECTED
        self.logger.info(f"Disconnected from {self.config.name}")
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if self.status != ServerStatus.CONNECTED or not self.session:
            raise ConnectionError(f"Not connected to {self.config.name}")
        
        url = f"{self.config.protocol}://{self.config.host}:{self.config.port}/tools/{tool_name}"
        
        try:
            async with self.session.post(url, json=parameters) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Tool call failed: {error_text}")
                    
        except Exception as e:
            self.logger.error(f"Tool call failed for {tool_name}: {e}")
            raise
    
    async def health_check(self) -> bool:
        if not self.session:
            return False
            
        url = f"{self.config.protocol}://{self.config.host}:{self.config.port}/health"
        
        try:
            async with self.session.get(url) as response:
                return response.status == 200
        except:
            return False


class MCPClientManager:
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.configs: Dict[str, MCPServerConfig] = {}
        self.logger = logging.getLogger("mcp.manager")
        
        # Initialize default server configurations
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        self.configs = {
            "arxiv": MCPServerConfig(
                name="arxiv",
                port=3001,
                tools=["search_papers", "get_paper", "get_latex_source"]
            ),
            "playwright": MCPServerConfig(
                name="playwright",
                port=3002,
                tools=["screenshot", "navigate", "extract_content"]
            ),
            "unstructured": MCPServerConfig(
                name="unstructured",
                port=3003,
                tools=["extract_pdf", "extract_html", "preprocess_text"]
            ),
            "fetch": MCPServerConfig(
                name="fetch",
                port=3004,
                tools=["fetch_url", "fetch_content", "convert_to_markdown"]
            ),
            "tinybird": MCPServerConfig(
                name="tinybird",
                port=3005,
                tools=["query_data", "insert_data", "analyze_performance"]
            ),
            "piloty": MCPServerConfig(
                name="piloty",
                port=3006,
                tools=["run_command", "schedule_task", "monitor_process"]
            )
        }
    
    async def connect_server(self, server_name: str) -> bool:
        if server_name not in self.configs:
            self.logger.error(f"Unknown server: {server_name}")
            return False
        
        config = self.configs[server_name]
        client = HTTPMCPClient(config)
        
        if await client.connect():
            self.clients[server_name] = client
            return True
        else:
            return False
    
    async def connect_all_servers(self) -> Dict[str, bool]:
        results = {}
        
        for server_name in self.configs:
            results[server_name] = await self.connect_server(server_name)
        
        connected_count = sum(results.values())
        self.logger.info(f"Connected to {connected_count}/{len(self.configs)} servers")
        
        return results
    
    async def disconnect_server(self, server_name: str) -> None:
        if server_name in self.clients:
            await self.clients[server_name].disconnect()
            del self.clients[server_name]
    
    async def disconnect_all_servers(self) -> None:
        for server_name in list(self.clients.keys()):
            await self.disconnect_server(server_name)
    
    async def call_tool(self, server_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if server_name not in self.clients:
            raise ConnectionError(f"Server {server_name} not connected")
        
        client = self.clients[server_name]
        return await client.call_tool(tool_name, parameters)
    
    def get_server_status(self, server_name: str) -> ServerStatus:
        if server_name in self.clients:
            return self.clients[server_name].status
        else:
            return ServerStatus.DISCONNECTED
    
    def get_all_server_status(self) -> Dict[str, ServerStatus]:
        return {
            name: self.get_server_status(name)
            for name in self.configs.keys()
        }
    
    async def health_check_all(self) -> Dict[str, bool]:
        results = {}
        
        for server_name, client in self.clients.items():
            try:
                results[server_name] = await client.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for {server_name}: {e}")
                results[server_name] = False
        
        return results
    
    def get_available_tools(self, server_name: str) -> List[str]:
        if server_name in self.configs:
            return self.configs[server_name].tools
        else:
            return []
    
    def is_server_connected(self, server_name: str) -> bool:
        return (server_name in self.clients and 
                self.clients[server_name].status == ServerStatus.CONNECTED)


# Global instance for use across agents
mcp_manager = MCPClientManager()