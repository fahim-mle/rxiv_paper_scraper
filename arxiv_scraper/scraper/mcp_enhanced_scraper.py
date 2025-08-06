"""
Enhanced Scraper Agent with MCP Server integration.
Uses Unstructured MCP and arXiv MCP for content parsing and metadata extraction.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import json
import re

from ..mcp_servers.client_manager import mcp_manager
from ..utils.logger import get_logger


@dataclass
class ScrapedPaper:
    title: str
    authors: List[str]
    abstract: str
    pdf_url: Optional[str] = None
    source_url: Optional[str] = None
    doi: Optional[str] = None
    categories: List[str] = None
    date_published: Optional[datetime] = None
    date_scraped: datetime = None
    raw_metadata: Dict[str, Any] = None
    processed_text: Optional[str] = None
    
    def __post_init__(self):
        if self.date_scraped is None:
            self.date_scraped = datetime.utcnow()
        if self.categories is None:
            self.categories = []
        if self.raw_metadata is None:
            self.raw_metadata = {}


@dataclass
class ScrapingResult:
    papers: List[ScrapedPaper]
    success: bool
    processed_count: int
    error_count: int
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class MCPEnhancedScraperAgent:
    def __init__(self):
        self.logger = get_logger(__name__)
        
    async def initialize(self) -> bool:
        """Initialize MCP connections required for scraping."""
        required_servers = ["unstructured", "arxiv"]
        connection_results = {}
        
        for server in required_servers:
            connection_results[server] = await mcp_manager.connect_server(server)
        
        success_count = sum(connection_results.values())
        self.logger.info(f"Connected to {success_count}/{len(required_servers)} scraper MCP servers")
        
        return success_count >= 1  # At least one server needed
    
    async def parse_metadata(self, raw_data: List[Dict[str, Any]], 
                           source: str = "unknown") -> ScrapingResult:
        """
        Parse raw metadata into structured paper objects.
        
        Args:
            raw_data: List of raw paper data dictionaries
            source: Source of the data (arxiv, web, etc.)
        """
        papers = []
        errors = []
        
        for i, data in enumerate(raw_data):
            try:
                paper = await self._parse_single_metadata(data, source)
                if paper:
                    papers.append(paper)
                    
            except Exception as e:
                error_msg = f"Metadata parsing failed for item {i}: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        self.logger.info(f"Parsed {len(papers)} papers from {len(raw_data)} raw items")
        
        return ScrapingResult(
            papers=papers,
            success=len(papers) > 0,
            processed_count=len(papers),
            error_count=len(errors),
            errors=errors
        )
    
    async def extract_pdf_text(self, pdf_urls: List[str]) -> Dict[str, str]:
        """
        Extract text from PDF files using Unstructured MCP.
        
        Args:
            pdf_urls: List of PDF URLs to process
            
        Returns:
            Dictionary mapping PDF URLs to extracted text
        """
        if not mcp_manager.is_server_connected("unstructured"):
            self.logger.warning("Unstructured MCP server not connected, skipping PDF extraction")
            return {}
        
        extracted_texts = {}
        
        for url in pdf_urls:
            try:
                response = await mcp_manager.call_tool(
                    "unstructured",
                    "extract_pdf",
                    {
                        "url": url,
                        "strategy": "auto",
                        "extract_images": False,
                        "chunk_elements": True
                    }
                )
                
                if response.get("success") and response.get("elements"):
                    # Combine text elements
                    text_parts = []
                    for element in response["elements"]:
                        if element.get("text"):
                            text_parts.append(element["text"])
                    
                    extracted_texts[url] = " ".join(text_parts)
                    self.logger.info(f"Extracted text from PDF: {url}")
                
            except Exception as e:
                self.logger.error(f"PDF extraction failed for {url}: {e}")
                
        return extracted_texts
    
    async def extract_html_content(self, html_content: str, source_url: str) -> ScrapedPaper:
        """
        Extract structured data from HTML content using Unstructured MCP.
        
        Args:
            html_content: Raw HTML content
            source_url: Source URL for the content
        """
        if not mcp_manager.is_server_connected("unstructured"):
            # Fallback to basic HTML parsing
            return await self._basic_html_parse(html_content, source_url)
        
        try:
            response = await mcp_manager.call_tool(
                "unstructured",
                "extract_html",
                {
                    "html": html_content,
                    "include_metadata": True,
                    "chunking_strategy": "by_title"
                }
            )
            
            if response.get("success") and response.get("elements"):
                return await self._build_paper_from_elements(
                    response["elements"], 
                    source_url
                )
                
        except Exception as e:
            self.logger.error(f"HTML extraction failed: {e}")
            
        # Fallback to basic parsing
        return await self._basic_html_parse(html_content, source_url)
    
    async def clean_data(self, papers: List[ScrapedPaper]) -> List[ScrapedPaper]:
        """
        Clean and normalize paper data.
        
        Args:
            papers: List of scraped papers to clean
        """
        cleaned_papers = []
        
        for paper in papers:
            try:
                cleaned_paper = await self._clean_single_paper(paper)
                if self._is_valid_paper(cleaned_paper):
                    cleaned_papers.append(cleaned_paper)
                else:
                    self.logger.warning(f"Paper failed validation: {paper.title[:50]}...")
                    
            except Exception as e:
                self.logger.error(f"Data cleaning failed for paper: {e}")
        
        self.logger.info(f"Cleaned {len(cleaned_papers)} papers from {len(papers)} input papers")
        
        return cleaned_papers
    
    async def preprocess_for_nlp(self, papers: List[ScrapedPaper]) -> List[Dict[str, Any]]:
        """
        Preprocess papers for NLP/ML applications using Unstructured MCP.
        
        Args:
            papers: List of scraped papers to preprocess
            
        Returns:
            List of preprocessed paper data for ML
        """
        if not mcp_manager.is_server_connected("unstructured"):
            self.logger.warning("Unstructured MCP not connected, using basic preprocessing")
            return [self._basic_nlp_preprocessing(paper) for paper in papers]
        
        preprocessed_papers = []
        
        for paper in papers:
            try:
                # Combine title, abstract, and any processed text
                full_text = f"{paper.title}\n\n{paper.abstract}"
                if paper.processed_text:
                    full_text += f"\n\n{paper.processed_text}"
                
                response = await mcp_manager.call_tool(
                    "unstructured",
                    "preprocess_text",
                    {
                        "text": full_text,
                        "clean": True,
                        "normalize": True,
                        "extract_keywords": True,
                        "split_sentences": True
                    }
                )
                
                if response.get("success"):
                    preprocessed_data = {
                        "paper_id": f"{paper.source_url or paper.title}_{paper.date_scraped}",
                        "title": paper.title,
                        "authors": paper.authors,
                        "abstract": paper.abstract,
                        "categories": paper.categories,
                        "date_published": paper.date_published.isoformat() if paper.date_published else None,
                        "preprocessed_text": response.get("cleaned_text", full_text),
                        "keywords": response.get("keywords", []),
                        "sentences": response.get("sentences", []),
                        "metadata": paper.raw_metadata
                    }
                    preprocessed_papers.append(preprocessed_data)
                
            except Exception as e:
                self.logger.error(f"NLP preprocessing failed for paper: {e}")
                # Add basic preprocessing as fallback
                preprocessed_papers.append(self._basic_nlp_preprocessing(paper))
        
        return preprocessed_papers
    
    async def _parse_single_metadata(self, data: Dict[str, Any], 
                                   source: str) -> Optional[ScrapedPaper]:
        """Parse single metadata entry into ScrapedPaper."""
        try:
            # Handle arXiv-specific format
            if source == "arxiv" or "arxiv_id" in data:
                return await self._parse_arxiv_metadata(data)
            
            # Handle web/generic format
            return await self._parse_generic_metadata(data, source)
            
        except Exception as e:
            self.logger.error(f"Single metadata parsing failed: {e}")
            return None
    
    async def _parse_arxiv_metadata(self, data: Dict[str, Any]) -> ScrapedPaper:
        """Parse arXiv-specific metadata format."""
        # Use arXiv MCP server for enhanced parsing if available
        if mcp_manager.is_server_connected("arxiv"):
            try:
                arxiv_id = data.get("id", "").split("/")[-1]  # Extract ID from URL
                
                response = await mcp_manager.call_tool(
                    "arxiv",
                    "get_paper",
                    {"arxiv_id": arxiv_id}
                )
                
                if response.get("success"):
                    arxiv_data = response["paper"]
                    return ScrapedPaper(
                        title=arxiv_data.get("title", ""),
                        authors=arxiv_data.get("authors", []),
                        abstract=arxiv_data.get("summary", ""),
                        pdf_url=arxiv_data.get("pdf_url"),
                        source_url=arxiv_data.get("entry_id"),
                        doi=arxiv_data.get("doi"),
                        categories=arxiv_data.get("categories", []),
                        date_published=self._parse_date(arxiv_data.get("published")),
                        raw_metadata=arxiv_data
                    )
                    
            except Exception as e:
                self.logger.error(f"arXiv MCP parsing failed: {e}")
        
        # Fallback to basic arXiv parsing
        return ScrapedPaper(
            title=data.get("title", ""),
            authors=data.get("authors", []),
            abstract=data.get("summary", ""),
            pdf_url=data.get("pdf_url"),
            source_url=data.get("id"),
            categories=data.get("categories", []),
            date_published=self._parse_date(data.get("published")),
            raw_metadata=data
        )
    
    async def _parse_generic_metadata(self, data: Dict[str, Any], 
                                    source: str) -> ScrapedPaper:
        """Parse generic metadata format."""
        return ScrapedPaper(
            title=data.get("title", ""),
            authors=data.get("authors", []),
            abstract=data.get("abstract", data.get("summary", "")),
            pdf_url=data.get("pdf_url"),
            source_url=data.get("source_url", data.get("url")),
            doi=data.get("doi"),
            categories=data.get("categories", []),
            date_published=self._parse_date(data.get("date_published", data.get("date"))),
            raw_metadata=data
        )
    
    async def _build_paper_from_elements(self, elements: List[Dict], 
                                       source_url: str) -> ScrapedPaper:
        """Build ScrapedPaper from Unstructured elements."""
        title = ""
        abstract = ""
        content_parts = []
        
        for element in elements:
            element_type = element.get("type", "")
            text = element.get("text", "")
            
            if element_type == "Title" and not title:
                title = text
            elif element_type == "NarrativeText" and "abstract" in text.lower():
                abstract = text
            elif text:
                content_parts.append(text)
        
        # If no abstract found in elements, try to extract from content
        if not abstract and content_parts:
            for part in content_parts:
                if "abstract" in part.lower():
                    abstract = part
                    break
        
        return ScrapedPaper(
            title=title or "Extracted Content",
            authors=[],  # Would need more sophisticated extraction
            abstract=abstract or (content_parts[0] if content_parts else ""),
            source_url=source_url,
            processed_text=" ".join(content_parts),
            raw_metadata={"elements": elements}
        )
    
    async def _basic_html_parse(self, html_content: str, source_url: str) -> ScrapedPaper:
        """Basic HTML parsing fallback."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title = ""
        if soup.title:
            title = soup.title.get_text()
        
        # Try to find abstract
        abstract = ""
        abstract_elem = soup.find(string=re.compile("abstract", re.IGNORECASE))
        if abstract_elem:
            abstract = abstract_elem.get_text()
        
        return ScrapedPaper(
            title=title,
            authors=[],
            abstract=abstract,
            source_url=source_url,
            raw_metadata={"html_length": len(html_content)}
        )
    
    async def _clean_single_paper(self, paper: ScrapedPaper) -> ScrapedPaper:
        """Clean a single paper's data."""
        # Clean title
        paper.title = re.sub(r'\s+', ' ', paper.title).strip()
        
        # Clean abstract
        paper.abstract = re.sub(r'\s+', ' ', paper.abstract).strip()
        
        # Clean authors
        paper.authors = [author.strip() for author in paper.authors if author.strip()]
        
        # Clean categories
        paper.categories = [cat.strip() for cat in paper.categories if cat.strip()]
        
        return paper
    
    def _is_valid_paper(self, paper: ScrapedPaper) -> bool:
        """Validate that paper has minimum required data."""
        return (
            len(paper.title.strip()) > 5 and
            len(paper.abstract.strip()) > 20 and
            (paper.pdf_url or paper.source_url)
        )
    
    def _basic_nlp_preprocessing(self, paper: ScrapedPaper) -> Dict[str, Any]:
        """Basic NLP preprocessing fallback."""
        return {
            "paper_id": f"{paper.source_url or paper.title}_{paper.date_scraped}",
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract,
            "categories": paper.categories,
            "date_published": paper.date_published.isoformat() if paper.date_published else None,
            "full_text": f"{paper.title} {paper.abstract} {paper.processed_text or ''}".strip(),
            "metadata": paper.raw_metadata
        }
    
    def _parse_date(self, date_str: Union[str, datetime, None]) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        # Try common date formats
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%a, %d %b %Y %H:%M:%S %Z"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse date: {date_str}")
        return None
    
    async def get_server_status(self) -> Dict[str, str]:
        """Get status of MCP servers used by scraper."""
        servers = ["unstructured", "arxiv"]
        return {
            server: mcp_manager.get_server_status(server).value
            for server in servers
        }
    
    async def shutdown(self):
        """Clean shutdown of scraper agent."""
        self.logger.info("Shutting down Enhanced Scraper Agent")