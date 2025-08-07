"""
arXiv API Crawler for AI/ML Papers

Implements the crawler agent for discovering and retrieving academic papers
from the arXiv API with focus on AI, ML, and computer science topics.
"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote_plus

import aiohttp
from ..utils.rate_limiter import RateLimiter
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ArxivAPIClient:
    """Client for interacting with the arXiv API."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    NAMESPACE = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    
    # AI/ML related categories for focused crawling
    AI_ML_CATEGORIES = [
        "cs.AI",  # Artificial Intelligence
        "cs.LG",  # Machine Learning
        "cs.CV",  # Computer Vision
        "cs.CL",  # Computation and Language
        "cs.NE",  # Neural and Evolutionary Computing
        "stat.ML",  # Machine Learning (Statistics)
        "cs.IR",  # Information Retrieval
        "cs.RO",  # Robotics
        "cs.HC",  # Human-Computer Interaction
        "cs.SD",  # Sound (includes speech recognition)
    ]
    
    def __init__(self, rate_limit_delay: float = 3.0):
        """
        Initialize arXiv API client.
        
        Args:
            rate_limit_delay: Delay between API requests (arXiv requires 3+ seconds)
        """
        self.rate_limiter = RateLimiter(delay=rate_limit_delay)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "arXiv-Scraper/1.0 (Research Purpose; Contact: admin@example.com)"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def build_search_query(self, 
                          categories: List[str] = None, 
                          keywords: List[str] = None,
                          date_from: datetime = None,
                          date_to: datetime = None,
                          max_results: int = 100) -> str:
        """
        Build arXiv API search query.
        
        Args:
            categories: List of arXiv categories to search
            keywords: Keywords to search in title/abstract
            date_from: Start date for papers
            date_to: End date for papers
            max_results: Maximum number of results
            
        Returns:
            Formatted query string for arXiv API
        """
        # Simplified query - just use categories without complex date filtering
        if categories:
            # Use OR to get papers from any of the specified categories
            category_query = " OR ".join([f"cat:{cat}" for cat in categories])
            search_query = f"({category_query})"
        else:
            search_query = "cat:cs.AI"
        
        # Build basic query parameters without date filtering initially
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": min(max_results, 2000),  # arXiv API limit
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        # Convert to query string
        query_string = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        return f"{self.BASE_URL}?{query_string}"
    
    async def fetch_papers(self, 
                          categories: List[str] = None,
                          keywords: List[str] = None,
                          max_results: int = 100,
                          days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch papers from arXiv API.
        
        Args:
            categories: arXiv categories to search (defaults to AI/ML categories)
            keywords: Additional keywords to search for
            max_results: Maximum number of papers to fetch
            days_back: How many days back to search
            
        Returns:
            List of paper metadata dictionaries
        """
        if not categories:
            categories = self.AI_ML_CATEGORIES
        
        # Build query without date filtering for now
        query_url = self.build_search_query(
            categories=categories,
            keywords=keywords,
            max_results=max_results
        )
        
        logger.info(f"Fetching papers from arXiv API: {len(categories)} categories, max {max_results} results")
        logger.debug(f"Query URL: {query_url}")
        
        try:
            await self.rate_limiter.wait()
            
            async with self.session.get(query_url) as response:
                if response.status != 200:
                    logger.error(f"arXiv API request failed: {response.status}")
                    return []
                
                xml_content = await response.text()
                return self.parse_arxiv_response(xml_content)
                
        except Exception as e:
            logger.error(f"Error fetching papers from arXiv: {e}")
            return []
    
    def parse_arxiv_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse XML response from arXiv API.
        
        Args:
            xml_content: XML response from arXiv API
            
        Returns:
            List of parsed paper metadata
        """
        try:
            root = ET.fromstring(xml_content)
            papers = []
            
            entries = root.findall(".//atom:entry", self.NAMESPACE)
            logger.info(f"Parsing {len(entries)} papers from arXiv response")
            
            for entry in entries:
                paper_data = self.parse_paper_entry(entry)
                if paper_data:
                    papers.append(paper_data)
            
            return papers
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse arXiv XML response: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing arXiv response: {e}")
            return []
    
    def parse_paper_entry(self, entry: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parse a single paper entry from arXiv XML.
        
        Args:
            entry: XML entry element for a paper
            
        Returns:
            Paper metadata dictionary or None if parsing fails
        """
        try:
            # Extract basic information
            arxiv_id = self.extract_arxiv_id(entry.find("atom:id", self.NAMESPACE))
            if not arxiv_id:
                return None
            
            title = self.clean_text(entry.find("atom:title", self.NAMESPACE))
            summary = self.clean_text(entry.find("atom:summary", self.NAMESPACE))
            
            # Extract authors
            authors = []
            for author in entry.findall(".//atom:author", self.NAMESPACE):
                name_elem = author.find("atom:name", self.NAMESPACE)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            
            # Extract categories
            categories = []
            for category in entry.findall(".//arxiv:primary_category", self.NAMESPACE):
                if category.get("term"):
                    categories.append(category.get("term"))
            
            for category in entry.findall(".//atom:category", self.NAMESPACE):
                if category.get("term") and category.get("term") not in categories:
                    categories.append(category.get("term"))
            
            # Extract dates
            published = self.parse_date(entry.find("atom:published", self.NAMESPACE))
            updated = self.parse_date(entry.find("atom:updated", self.NAMESPACE))
            
            # Extract PDF link
            pdf_url = None
            for link in entry.findall("atom:link", self.NAMESPACE):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href")
                    break
            
            # Build paper data structure
            paper_data = {
                "paper_id": arxiv_id,
                "source": "arxiv",
                "title": title,
                "authors": authors,
                "abstract": summary,
                "categories": categories,
                "date_published": published,
                "date_updated": updated,
                "pdf_url": pdf_url,
                "pdf_downloaded": False,
                "pdf_file_path": None,
                "pdf_file_size": None,
                "source_metadata": {
                    "arxiv_id": arxiv_id,
                    "primary_category": categories[0] if categories else None,
                    "all_categories": categories,
                    "entry_id": entry.find("atom:id", self.NAMESPACE).text if entry.find("atom:id", self.NAMESPACE) is not None else None,
                },
                "processing_status": "pending"
            }
            
            return paper_data
            
        except Exception as e:
            logger.warning(f"Failed to parse paper entry: {e}")
            return None
    
    def extract_arxiv_id(self, id_element: Optional[ET.Element]) -> Optional[str]:
        """Extract arXiv ID from ID element."""
        if id_element is None or not id_element.text:
            return None
        
        # Extract arXiv ID from full URL
        match = re.search(r"arxiv\.org/abs/(.+)$", id_element.text)
        if match:
            return match.group(1)
        
        return None
    
    def clean_text(self, element: Optional[ET.Element]) -> str:
        """Clean and normalize text content."""
        if element is None or not element.text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', element.text.strip())
        return text
    
    def parse_date(self, date_element: Optional[ET.Element]) -> Optional[datetime]:
        """Parse date from XML element."""
        if date_element is None or not date_element.text:
            return None
        
        try:
            # arXiv uses ISO format: 2023-01-15T10:30:00Z
            date_str = date_element.text.strip()
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Failed to parse date {date_element.text}: {e}")
            return None


class ArxivCrawler:
    """Main crawler class for arXiv papers."""
    
    def __init__(self, rate_limit_delay: float = 3.0):
        """
        Initialize arXiv crawler.
        
        Args:
            rate_limit_delay: Delay between API requests
        """
        self.api_client = ArxivAPIClient(rate_limit_delay)
        self.logger = get_logger(self.__class__.__name__)
    
    async def crawl_ai_ml_papers(self, 
                                max_papers: int = 100,
                                days_back: int = 30,
                                additional_keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        Crawl AI/ML papers from arXiv.
        
        Args:
            max_papers: Maximum number of papers to crawl
            days_back: How many days back to search
            additional_keywords: Additional keywords to include in search
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Starting AI/ML paper crawl: max {max_papers} papers, {days_back} days back")
        
        # Define AI/ML focused keywords
        ai_ml_keywords = [
            "machine learning", "artificial intelligence", "deep learning",
            "neural network", "transformer", "large language model",
            "computer vision", "natural language processing", "reinforcement learning"
        ]
        
        if additional_keywords:
            ai_ml_keywords.extend(additional_keywords)
        
        async with self.api_client:
            # Fetch papers with AI/ML categories and keywords
            papers = await self.api_client.fetch_papers(
                categories=ArxivAPIClient.AI_ML_CATEGORIES,
                keywords=ai_ml_keywords[:5],  # Limit keywords to avoid query complexity
                max_results=max_papers,
                days_back=days_back
            )
            
            self.logger.info(f"Crawled {len(papers)} AI/ML papers from arXiv")
            return papers
    
    async def crawl_specific_categories(self, 
                                      categories: List[str],
                                      max_papers: int = 100,
                                      days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Crawl papers from specific arXiv categories.
        
        Args:
            categories: List of arXiv categories to search
            max_papers: Maximum number of papers to crawl
            days_back: How many days back to search
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Starting category-specific crawl: {categories}")
        
        async with self.api_client:
            papers = await self.api_client.fetch_papers(
                categories=categories,
                max_results=max_papers,
                days_back=days_back
            )
            
            self.logger.info(f"Crawled {len(papers)} papers from categories: {categories}")
            return papers


# Convenience function for quick testing
async def crawl_test_papers(max_papers: int = 20) -> List[Dict[str, Any]]:
    """
    Quick function to crawl test papers for validation.
    
    Args:
        max_papers: Number of papers to crawl
        
    Returns:
        List of paper metadata dictionaries
    """
    crawler = ArxivCrawler()
    return await crawler.crawl_ai_ml_papers(max_papers=max_papers, days_back=7)