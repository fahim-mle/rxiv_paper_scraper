"""
Enhanced Crawler Agent with MCP Server integration.
Uses arXiv MCP, Fetch MCP, and Playwright MCP for content discovery.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..mcp_servers.client_manager import mcp_manager
from ..utils.logger import get_logger
from ..utils.rate_limiter import RateLimiter


@dataclass
class CrawlResult:
    source: str
    papers: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None
    crawl_timestamp: datetime = None
    
    def __post_init__(self):
        if self.crawl_timestamp is None:
            self.crawl_timestamp = datetime.utcnow()


class MCPEnhancedCrawlerAgent:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.rate_limiter = RateLimiter()
        self.arxiv_rate_limiter = RateLimiter(delay=3.0)  # arXiv requires 3s delay
        
    async def initialize(self) -> bool:
        """Initialize MCP connections required for crawling."""
        required_servers = ["arxiv", "fetch", "playwright"]
        connection_results = {}
        
        for server in required_servers:
            connection_results[server] = await mcp_manager.connect_server(server)
            
        success_count = sum(connection_results.values())
        self.logger.info(f"Connected to {success_count}/{len(required_servers)} required MCP servers")
        
        return success_count >= 2  # At least arxiv and one other server
    
    async def crawl_arxiv(self, query: str = "cat:cs.AI", max_results: int = 100,
                         date_range: tuple = None) -> CrawlResult:
        """
        Crawl arXiv using the arXiv MCP server.
        
        Args:
            query: arXiv search query (e.g., "cat:cs.AI", "machine learning")
            max_results: Maximum number of papers to fetch
            date_range: Tuple of (start_date, end_date) as strings
        """
        if not mcp_manager.is_server_connected("arxiv"):
            return CrawlResult(
                source="arxiv",
                papers=[],
                success=False,
                error_message="ArXiv MCP server not connected"
            )
        
        try:
            await self.arxiv_rate_limiter.wait()
            
            parameters = {
                "query": query,
                "max_results": max_results
            }
            
            if date_range:
                parameters["date_from"] = date_range[0]
                parameters["date_to"] = date_range[1]
            
            response = await mcp_manager.call_tool("arxiv", "search_papers", parameters)
            
            papers = response.get("papers", [])
            self.logger.info(f"Crawled {len(papers)} papers from arXiv with query: {query}")
            
            return CrawlResult(
                source="arxiv",
                papers=papers,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"arXiv crawl failed: {e}")
            return CrawlResult(
                source="arxiv",
                papers=[],
                success=False,
                error_message=str(e)
            )
    
    async def crawl_web_sources(self, urls: List[str]) -> CrawlResult:
        """
        Crawl web sources using Playwright MCP for JavaScript-heavy sites.
        
        Args:
            urls: List of URLs to crawl
        """
        if not mcp_manager.is_server_connected("playwright"):
            return CrawlResult(
                source="web_playwright",
                papers=[],
                success=False,
                error_message="Playwright MCP server not connected"
            )
        
        papers = []
        errors = []
        
        for url in urls:
            try:
                await self.rate_limiter.wait()
                
                # Navigate to URL and extract content
                nav_response = await mcp_manager.call_tool(
                    "playwright", 
                    "navigate", 
                    {"url": url, "wait_for": "networkidle"}
                )
                
                if nav_response.get("success"):
                    # Extract content from the page
                    extract_response = await mcp_manager.call_tool(
                        "playwright",
                        "extract_content",
                        {"selectors": ["article", ".paper", ".publication"]}
                    )
                    
                    if extract_response.get("content"):
                        paper_data = self._parse_web_content(extract_response["content"], url)
                        papers.append(paper_data)
                
            except Exception as e:
                self.logger.error(f"Web crawl failed for {url}: {e}")
                errors.append(f"{url}: {str(e)}")
        
        success = len(papers) > 0
        error_message = "; ".join(errors) if errors else None
        
        self.logger.info(f"Crawled {len(papers)} papers from {len(urls)} web sources")
        
        return CrawlResult(
            source="web_playwright",
            papers=papers,
            success=success,
            error_message=error_message
        )
    
    async def fetch_content_urls(self, urls: List[str]) -> CrawlResult:
        """
        Fetch content from URLs using Fetch MCP server.
        
        Args:
            urls: List of URLs to fetch content from
        """
        if not mcp_manager.is_server_connected("fetch"):
            return CrawlResult(
                source="fetch",
                papers=[],
                success=False,
                error_message="Fetch MCP server not connected"
            )
        
        papers = []
        errors = []
        
        for url in urls:
            try:
                await self.rate_limiter.wait()
                
                response = await mcp_manager.call_tool(
                    "fetch",
                    "fetch_content",
                    {"url": url, "format": "markdown"}
                )
                
                if response.get("content"):
                    paper_data = self._parse_fetched_content(response["content"], url)
                    papers.append(paper_data)
                    
            except Exception as e:
                self.logger.error(f"Fetch failed for {url}: {e}")
                errors.append(f"{url}: {str(e)}")
        
        success = len(papers) > 0
        error_message = "; ".join(errors) if errors else None
        
        self.logger.info(f"Fetched {len(papers)} papers from {len(urls)} URLs")
        
        return CrawlResult(
            source="fetch",
            papers=papers,
            success=success,
            error_message=error_message
        )
    
    async def extract_paper_urls(self, source_urls: List[str]) -> List[str]:
        """
        Extract paper URLs from source pages using available MCP servers.
        
        Args:
            source_urls: URLs of pages containing paper links
            
        Returns:
            List of extracted paper URLs
        """
        paper_urls = []
        
        for url in source_urls:
            try:
                if mcp_manager.is_server_connected("playwright"):
                    # Use Playwright for JavaScript-heavy pages
                    await mcp_manager.call_tool(
                        "playwright",
                        "navigate",
                        {"url": url}
                    )
                    
                    response = await mcp_manager.call_tool(
                        "playwright",
                        "extract_content",
                        {"selectors": ["a[href*='pdf']", "a[href*='paper']", "a[href*='arxiv']"]}
                    )
                    
                    if response.get("links"):
                        paper_urls.extend(response["links"])
                
                elif mcp_manager.is_server_connected("fetch"):
                    # Use Fetch MCP as fallback
                    response = await mcp_manager.call_tool(
                        "fetch",
                        "fetch_url",
                        {"url": url}
                    )
                    
                    # Basic URL extraction from content
                    content = response.get("content", "")
                    extracted_urls = self._extract_urls_from_content(content)
                    paper_urls.extend(extracted_urls)
                    
            except Exception as e:
                self.logger.error(f"URL extraction failed for {url}: {e}")
        
        # Remove duplicates and filter valid URLs
        unique_urls = list(set(paper_urls))
        valid_urls = [url for url in unique_urls if self._is_valid_paper_url(url)]
        
        self.logger.info(f"Extracted {len(valid_urls)} paper URLs from {len(source_urls)} source pages")
        
        return valid_urls
    
    def _parse_web_content(self, content: str, source_url: str) -> Dict[str, Any]:
        """Parse web content into paper metadata."""
        # Basic parsing - this would be enhanced based on specific site structures
        return {
            "title": "Extracted from web",  # Would extract actual title
            "authors": [],  # Would extract actual authors
            "abstract": content[:500] + "..." if len(content) > 500 else content,
            "source_url": source_url,
            "source": "web_crawler",
            "date_crawled": datetime.utcnow().isoformat(),
            "content_preview": content[:1000]
        }
    
    def _parse_fetched_content(self, content: str, source_url: str) -> Dict[str, Any]:
        """Parse fetched markdown content into paper metadata."""
        # Basic parsing for markdown content
        lines = content.split('\n')
        title = lines[0].replace('#', '').strip() if lines else "Fetched Content"
        
        return {
            "title": title,
            "authors": [],  # Would extract from content
            "abstract": content[:500] + "..." if len(content) > 500 else content,
            "source_url": source_url,
            "source": "fetch_crawler",
            "date_crawled": datetime.utcnow().isoformat(),
            "markdown_content": content
        }
    
    def _extract_urls_from_content(self, content: str) -> List[str]:
        """Extract URLs from HTML/text content."""
        import re
        
        # Basic URL extraction patterns
        url_patterns = [
            r'https?://arxiv\.org/[^\s<>"]+',
            r'https?://[^\s<>"]*\.pdf[^\s<>"]*',
            r'https?://[^\s<>"]*paper[^\s<>"]*'
        ]
        
        urls = []
        for pattern in url_patterns:
            urls.extend(re.findall(pattern, content))
        
        return urls
    
    def _is_valid_paper_url(self, url: str) -> bool:
        """Check if URL likely points to a paper."""
        paper_indicators = [
            'arxiv.org',
            '.pdf',
            'paper',
            'publication',
            'doi.org'
        ]
        
        return any(indicator in url.lower() for indicator in paper_indicators)
    
    async def get_server_status(self) -> Dict[str, str]:
        """Get status of all MCP servers used by crawler."""
        servers = ["arxiv", "fetch", "playwright"]
        return {
            server: mcp_manager.get_server_status(server).value
            for server in servers
        }
    
    async def shutdown(self):
        """Clean shutdown of crawler agent."""
        self.logger.info("Shutting down Enhanced Crawler Agent")
        # MCP manager handles server disconnection globally