"""
Metadata Parser for arXiv Papers

Handles parsing and validation of paper metadata from various sources.
Ensures data quality and consistency before database storage.
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MetadataValidator:
    """Validates and cleans paper metadata."""
    
    # Required fields for paper metadata
    REQUIRED_FIELDS = {
        "paper_id", "source", "title", "authors", "abstract", 
        "categories", "date_published", "pdf_url"
    }
    
    # Valid sources
    VALID_SOURCES = {"arxiv", "journal", "preprint", "conference"}
    
    # arXiv ID pattern
    ARXIV_ID_PATTERN = re.compile(r'^(\d{4}\.\d{4,5})(v\d+)?$')
    
    @classmethod
    def validate_paper(cls, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean paper metadata.
        
        Args:
            paper_data: Raw paper metadata dictionary
            
        Returns:
            Cleaned and validated paper metadata
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        validated_data = paper_data.copy()
        
        # Check required fields
        missing_fields = cls.REQUIRED_FIELDS - set(paper_data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Validate and clean individual fields
        validated_data["paper_id"] = cls._validate_paper_id(paper_data["paper_id"], paper_data["source"])
        validated_data["source"] = cls._validate_source(paper_data["source"])
        validated_data["title"] = cls._clean_title(paper_data["title"])
        validated_data["authors"] = cls._validate_authors(paper_data["authors"])
        validated_data["abstract"] = cls._clean_abstract(paper_data["abstract"])
        validated_data["categories"] = cls._validate_categories(paper_data["categories"])
        validated_data["date_published"] = cls._validate_date(paper_data["date_published"])
        validated_data["pdf_url"] = cls._validate_url(paper_data["pdf_url"])
        
        # Handle optional fields
        if "date_updated" in paper_data and paper_data["date_updated"]:
            validated_data["date_updated"] = cls._validate_date(paper_data["date_updated"])
        
        # Ensure default values for processing fields
        validated_data.setdefault("pdf_downloaded", False)
        validated_data.setdefault("processing_status", "pending")
        validated_data.setdefault("source_metadata", {})
        
        return validated_data
    
    @classmethod
    def _validate_paper_id(cls, paper_id: str, source: str) -> str:
        """Validate paper ID based on source."""
        if not paper_id or not isinstance(paper_id, str):
            raise ValueError("Paper ID must be a non-empty string")
        
        paper_id = paper_id.strip()
        
        if source == "arxiv":
            # Validate arXiv ID format
            if not cls.ARXIV_ID_PATTERN.match(paper_id):
                raise ValueError(f"Invalid arXiv ID format: {paper_id}")
        
        return paper_id
    
    @classmethod
    def _validate_source(cls, source: str) -> str:
        """Validate source type."""
        if not source or not isinstance(source, str):
            raise ValueError("Source must be a non-empty string")
        
        source = source.lower().strip()
        
        if source not in cls.VALID_SOURCES:
            logger.warning(f"Unknown source type: {source}")
        
        return source
    
    @classmethod
    def _clean_title(cls, title: str) -> str:
        """Clean and validate title."""
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        
        # Remove extra whitespace and normalize
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Remove trailing periods if they look like formatting artifacts
        title = re.sub(r'\.$', '', title)
        
        if len(title) < 10:
            logger.warning(f"Suspiciously short title: {title}")
        
        return title
    
    @classmethod
    def _validate_authors(cls, authors: List[str]) -> List[str]:
        """Validate and clean author list."""
        if not authors or not isinstance(authors, list):
            raise ValueError("Authors must be a non-empty list")
        
        cleaned_authors = []
        for author in authors:
            if isinstance(author, str) and author.strip():
                # Clean author name
                cleaned_name = re.sub(r'\s+', ' ', author.strip())
                # Remove common artifacts
                cleaned_name = re.sub(r'\([^)]*\)$', '', cleaned_name).strip()
                if cleaned_name:
                    cleaned_authors.append(cleaned_name)
        
        if not cleaned_authors:
            raise ValueError("No valid authors found")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_authors = []
        for author in cleaned_authors:
            if author not in seen:
                seen.add(author)
                unique_authors.append(author)
        
        return unique_authors
    
    @classmethod
    def _clean_abstract(cls, abstract: str) -> str:
        """Clean and validate abstract."""
        if not abstract or not isinstance(abstract, str):
            raise ValueError("Abstract must be a non-empty string")
        
        # Remove extra whitespace and normalize
        abstract = re.sub(r'\s+', ' ', abstract.strip())
        
        # Remove common prefixes
        abstract = re.sub(r'^(abstract:?\s*)', '', abstract, flags=re.IGNORECASE)
        
        if len(abstract) < 50:
            logger.warning(f"Suspiciously short abstract: {abstract[:100]}")
        
        return abstract
    
    @classmethod
    def _validate_categories(cls, categories: List[str]) -> List[str]:
        """Validate and clean categories."""
        if not categories or not isinstance(categories, list):
            return []
        
        cleaned_categories = []
        for category in categories:
            if isinstance(category, str) and category.strip():
                cleaned_cat = category.strip().lower()
                if cleaned_cat not in cleaned_categories:
                    cleaned_categories.append(cleaned_cat)
        
        return cleaned_categories
    
    @classmethod
    def _validate_date(cls, date_obj: Any) -> datetime:
        """Validate date object."""
        if isinstance(date_obj, datetime):
            return date_obj
        elif isinstance(date_obj, str):
            try:
                # Try parsing ISO format
                if date_obj.endswith('Z'):
                    date_obj = date_obj[:-1] + '+00:00'
                return datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid date format: {date_obj}")
        else:
            raise ValueError(f"Date must be datetime object or ISO string, got: {type(date_obj)}")
    
    @classmethod
    def _validate_url(cls, url: str) -> str:
        """Validate PDF URL."""
        if not url or not isinstance(url, str):
            raise ValueError("PDF URL must be a non-empty string")
        
        url = url.strip()
        
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError(f"Invalid URL format: {url}")
        except Exception:
            raise ValueError(f"Invalid URL: {url}")
        
        return url


class MetadataEnricher:
    """Enriches paper metadata with additional information."""
    
    @classmethod
    def enrich_arxiv_paper(cls, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich arXiv paper metadata with additional derived information.
        
        Args:
            paper_data: Basic paper metadata
            
        Returns:
            Enriched paper metadata
        """
        enriched_data = paper_data.copy()
        
        # Extract version from arXiv ID
        if paper_data["source"] == "arxiv":
            cls._extract_arxiv_version(enriched_data)
        
        # Classify paper type based on categories
        cls._classify_paper_type(enriched_data)
        
        # Extract keywords from title and abstract
        cls._extract_keywords(enriched_data)
        
        # Estimate reading time
        cls._estimate_reading_time(enriched_data)
        
        return enriched_data
    
    @classmethod
    def _extract_arxiv_version(cls, paper_data: Dict[str, Any]):
        """Extract version information from arXiv ID."""
        arxiv_id = paper_data.get("paper_id", "")
        version_match = re.search(r'v(\d+)$', arxiv_id)
        
        if version_match:
            version = int(version_match.group(1))
            base_id = arxiv_id.replace(f"v{version}", "")
        else:
            version = 1
            base_id = arxiv_id
        
        paper_data["source_metadata"]["version"] = version
        paper_data["source_metadata"]["base_id"] = base_id
    
    @classmethod
    def _classify_paper_type(cls, paper_data: Dict[str, Any]):
        """Classify paper type based on categories and content."""
        categories = paper_data.get("categories", [])
        title = paper_data.get("title", "").lower()
        abstract = paper_data.get("abstract", "").lower()
        
        paper_types = set()
        
        # AI/ML specific classifications
        if any(cat.startswith(("cs.ai", "cs.lg", "stat.ml")) for cat in categories):
            paper_types.add("machine_learning")
        
        if any(cat.startswith("cs.cv") for cat in categories):
            paper_types.add("computer_vision")
        
        if any(cat.startswith("cs.cl") for cat in categories):
            paper_types.add("natural_language_processing")
        
        # Check for survey/review papers
        if any(keyword in title for keyword in ["survey", "review", "systematic"]):
            paper_types.add("survey")
        
        # Check for theoretical papers
        if any(keyword in title for keyword in ["theory", "theoretical", "analysis"]):
            paper_types.add("theoretical")
        
        # Check for empirical papers
        if any(keyword in abstract for keyword in ["experiment", "empirical", "evaluation", "benchmark"]):
            paper_types.add("empirical")
        
        paper_data["source_metadata"]["paper_types"] = list(paper_types)
    
    @classmethod
    def _extract_keywords(cls, paper_data: Dict[str, Any]):
        """Extract potential keywords from title and abstract."""
        title = paper_data.get("title", "").lower()
        abstract = paper_data.get("abstract", "").lower()
        
        # Common AI/ML keywords to look for
        ai_ml_keywords = [
            "neural network", "deep learning", "machine learning", "artificial intelligence",
            "transformer", "attention", "bert", "gpt", "llm", "large language model",
            "computer vision", "natural language processing", "reinforcement learning",
            "supervised learning", "unsupervised learning", "semi-supervised",
            "classification", "regression", "clustering", "generative", "discriminative",
            "convolution", "recurrent", "lstm", "gru", "cnn", "rnn", "gan",
            "optimization", "gradient descent", "backpropagation", "fine-tuning"
        ]
        
        found_keywords = []
        text_to_search = f"{title} {abstract}"
        
        for keyword in ai_ml_keywords:
            if keyword in text_to_search:
                found_keywords.append(keyword)
        
        paper_data["source_metadata"]["detected_keywords"] = found_keywords[:10]  # Limit to top 10
    
    @classmethod
    def _estimate_reading_time(cls, paper_data: Dict[str, Any]):
        """Estimate reading time based on abstract length."""
        abstract = paper_data.get("abstract", "")
        word_count = len(abstract.split())
        
        # Rough estimate: 200 words per minute, plus base time for paper structure
        estimated_minutes = max(10, (word_count / 200) * 60 + 15)  # Minimum 10 minutes
        
        paper_data["source_metadata"]["estimated_reading_minutes"] = int(estimated_minutes)


class PaperMetadataProcessor:
    """Main processor for paper metadata."""
    
    def __init__(self):
        """Initialize metadata processor."""
        self.validator = MetadataValidator()
        self.enricher = MetadataEnricher()
        self.logger = get_logger(self.__class__.__name__)
    
    def process_paper_batch(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of papers.
        
        Args:
            papers: List of raw paper metadata
            
        Returns:
            List of processed and validated papers
        """
        processed_papers = []
        errors = []
        
        for i, paper in enumerate(papers):
            try:
                # Validate basic metadata
                validated_paper = self.validator.validate_paper(paper)
                
                # Enrich with additional metadata
                if validated_paper["source"] == "arxiv":
                    enriched_paper = self.enricher.enrich_arxiv_paper(validated_paper)
                else:
                    enriched_paper = validated_paper
                
                processed_papers.append(enriched_paper)
                
            except ValueError as e:
                error_msg = f"Paper {i}: Validation error - {e}"
                self.logger.warning(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Paper {i}: Processing error - {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        self.logger.info(f"Processed {len(processed_papers)}/{len(papers)} papers successfully")
        if errors:
            self.logger.warning(f"Encountered {len(errors)} errors during processing")
        
        return processed_papers
    
    def process_single_paper(self, paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single paper.
        
        Args:
            paper: Raw paper metadata
            
        Returns:
            Processed paper metadata or None if processing fails
        """
        try:
            validated_paper = self.validator.validate_paper(paper)
            
            if validated_paper["source"] == "arxiv":
                return self.enricher.enrich_arxiv_paper(validated_paper)
            else:
                return validated_paper
                
        except Exception as e:
            self.logger.error(f"Failed to process paper {paper.get('paper_id', 'unknown')}: {e}")
            return None