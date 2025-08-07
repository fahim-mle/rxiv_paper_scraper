"""
PDF Downloader for Academic Papers

Handles downloading PDF files from academic sources with rate limiting,
storage management, and file integrity verification.
"""

import asyncio
import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import aiohttp
import aiofiles

from ..utils.rate_limiter import RateLimiter
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StorageManager:
    """Manages PDF storage within the 300GB constraint."""
    
    def __init__(self, base_path: str = "papers", max_storage_gb: int = 300):
        """
        Initialize storage manager.
        
        Args:
            base_path: Base directory for storing papers
            max_storage_gb: Maximum storage limit in GB
        """
        self.base_path = Path(base_path).resolve()
        self.max_storage_bytes = max_storage_gb * 1024 * 1024 * 1024
        self.base_path.mkdir(exist_ok=True, parents=True)
        
        # Create subdirectories by source and category
        self.arxiv_path = self.base_path / "arxiv"
        self.arxiv_path.mkdir(exist_ok=True)
        
        self.logger = get_logger(self.__class__.__name__)
    
    def get_current_storage_usage(self) -> int:
        """Get current storage usage in bytes."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self.base_path):
                for filename in filenames:
                    if filename.endswith('.pdf'):
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
            return total_size
        except Exception as e:
            self.logger.error(f"Error calculating storage usage: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get detailed storage statistics."""
        current_usage = self.get_current_storage_usage()
        usage_gb = current_usage / (1024 * 1024 * 1024)
        max_gb = self.max_storage_bytes / (1024 * 1024 * 1024)
        
        return {
            "current_usage_bytes": current_usage,
            "current_usage_gb": round(usage_gb, 2),
            "max_storage_gb": max_gb,
            "usage_percentage": round((current_usage / self.max_storage_bytes) * 100, 1),
            "available_bytes": self.max_storage_bytes - current_usage,
            "available_gb": round((self.max_storage_bytes - current_usage) / (1024 * 1024 * 1024), 2)
        }
    
    def can_store_file(self, file_size: int) -> bool:
        """Check if we can store a file of given size."""
        current_usage = self.get_current_storage_usage()
        return (current_usage + file_size) <= self.max_storage_bytes
    
    def get_paper_file_path(self, paper_id: str, source: str = "arxiv") -> Path:
        """
        Generate file path for a paper PDF.
        
        Args:
            paper_id: Unique paper identifier
            source: Source of the paper
            
        Returns:
            Path object for the PDF file
        """
        # Sanitize paper ID for filename
        safe_id = "".join(c for c in paper_id if c.isalnum() or c in ".-_")
        
        if source == "arxiv":
            # Organize by arXiv category if available
            if "." in paper_id:
                # Extract year-month from ID (e.g., "2301.12345" -> "2301")
                year_month = paper_id.split(".")[0]
                category_path = self.arxiv_path / year_month
                category_path.mkdir(exist_ok=True)
                return category_path / f"{safe_id}.pdf"
            else:
                return self.arxiv_path / f"{safe_id}.pdf"
        else:
            # Other sources
            source_path = self.base_path / source
            source_path.mkdir(exist_ok=True)
            return source_path / f"{safe_id}.pdf"
    
    def cleanup_old_files(self, days_threshold: int = 90) -> int:
        """
        Clean up old files to free space.
        
        Args:
            days_threshold: Remove files older than this many days
            
        Returns:
            Number of files removed
        """
        removed_count = 0
        cutoff_time = datetime.now().timestamp() - (days_threshold * 24 * 60 * 60)
        
        try:
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            removed_count += 1
                            self.logger.info(f"Removed old file: {file}")
        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        return removed_count


class PDFDownloader:
    """Downloads PDF files from academic sources."""
    
    def __init__(self, storage_manager: StorageManager, rate_limit_delay: float = 1.0):
        """
        Initialize PDF downloader.
        
        Args:
            storage_manager: Storage manager instance
            rate_limit_delay: Delay between download requests
        """
        self.storage = storage_manager
        self.rate_limiter = RateLimiter(delay=rate_limit_delay)
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = get_logger(self.__class__.__name__)
        
        # Download statistics
        self.stats = {
            "attempted": 0,
            "successful": 0,
            "failed": 0,
            "skipped_storage": 0,
            "bytes_downloaded": 0
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),  # 5 minutes timeout
            headers={
                "User-Agent": "arXiv-Scraper/1.0 (Research Purpose; Contact: admin@example.com)"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def download_paper(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download PDF for a single paper.
        
        Args:
            paper_data: Paper metadata dictionary
            
        Returns:
            Updated paper metadata with download information
        """
        paper_id = paper_data["paper_id"]
        pdf_url = paper_data["pdf_url"]
        source = paper_data["source"]
        
        self.stats["attempted"] += 1
        
        # Check if already downloaded
        if paper_data.get("pdf_downloaded", False):
            self.logger.debug(f"Paper {paper_id} already downloaded")
            return paper_data
        
        try:
            # Generate file path
            file_path = self.storage.get_paper_file_path(paper_id, source)
            
            # Check if file already exists
            if file_path.exists():
                file_size = file_path.stat().st_size
                if file_size > 1000:  # If file is larger than 1KB, assume it's valid
                    paper_data.update({
                        "pdf_downloaded": True,
                        "pdf_file_path": str(file_path),
                        "pdf_file_size": file_size
                    })
                    self.logger.debug(f"Paper {paper_id} already exists on disk")
                    return paper_data
            
            # Download the PDF
            download_result = await self._download_file(pdf_url, file_path)
            
            if download_result["success"]:
                paper_data.update({
                    "pdf_downloaded": True,
                    "pdf_file_path": str(file_path),
                    "pdf_file_size": download_result["file_size"]
                })
                self.stats["successful"] += 1
                self.stats["bytes_downloaded"] += download_result["file_size"]
                self.logger.info(f"Successfully downloaded {paper_id} ({download_result['file_size']} bytes)")
            else:
                self.stats["failed"] += 1
                self.logger.error(f"Failed to download {paper_id}: {download_result['error']}")
                
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"Error downloading {paper_id}: {e}")
        
        return paper_data
    
    async def _download_file(self, url: str, file_path: Path) -> Dict[str, Any]:
        """
        Download a file from URL to local path.
        
        Args:
            url: URL to download from
            file_path: Local path to save file
            
        Returns:
            Dictionary with download result information
        """
        try:
            # Apply rate limiting
            await self.rate_limiter.wait()
            
            # Make HTTP request
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {response.reason}"
                    }
                
                # Check content type
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" not in content_type and not url.endswith(".pdf"):
                    # Still try to download, but log warning
                    self.logger.warning(f"Unexpected content type for {url}: {content_type}")
                
                # Get expected file size
                content_length = response.headers.get("content-length")
                expected_size = int(content_length) if content_length else None
                
                # Check if we have space for this file
                if expected_size and not self.storage.can_store_file(expected_size):
                    return {
                        "success": False,
                        "error": f"Insufficient storage space for file ({expected_size} bytes)"
                    }
                
                # Create directory if it doesn't exist
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download file in chunks
                total_size = 0
                hash_md5 = hashlib.md5()
                
                async with aiofiles.open(file_path, "wb") as file:
                    async for chunk in response.content.iter_chunked(8192):
                        await file.write(chunk)
                        total_size += len(chunk)
                        hash_md5.update(chunk)
                        
                        # Check storage limit during download
                        if not self.storage.can_store_file(0):  # Just check current usage
                            await file.close()
                            file_path.unlink()  # Remove partial file
                            return {
                                "success": False,
                                "error": "Storage limit exceeded during download"
                            }
                
                # Verify file size
                if expected_size and total_size != expected_size:
                    self.logger.warning(f"Size mismatch: expected {expected_size}, got {total_size}")
                
                # Basic PDF validation
                if not await self._validate_pdf_file(file_path):
                    file_path.unlink()  # Remove invalid file
                    return {
                        "success": False,
                        "error": "Downloaded file is not a valid PDF"
                    }
                
                return {
                    "success": True,
                    "file_size": total_size,
                    "md5_hash": hash_md5.hexdigest()
                }
                
        except asyncio.TimeoutError:
            return {"success": False, "error": "Download timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _validate_pdf_file(self, file_path: Path) -> bool:
        """
        Basic validation that file is a PDF.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file appears to be a valid PDF
        """
        try:
            # Check file size
            if file_path.stat().st_size < 1000:  # PDFs should be at least 1KB
                return False
            
            # Check PDF header
            async with aiofiles.open(file_path, "rb") as file:
                header = await file.read(8)
                if not header.startswith(b"%PDF-"):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating PDF {file_path}: {e}")
            return False
    
    async def download_papers_batch(self, papers: List[Dict[str, Any]], 
                                  max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        Download PDFs for a batch of papers with concurrency control.
        
        Args:
            papers: List of paper metadata dictionaries
            max_concurrent: Maximum concurrent downloads
            
        Returns:
            List of updated paper metadata
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(paper):
            async with semaphore:
                return await self.download_paper(paper)
        
        # Start downloads
        self.logger.info(f"Starting batch download of {len(papers)} papers (max {max_concurrent} concurrent)")
        
        tasks = [download_with_semaphore(paper) for paper in papers]
        updated_papers = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_papers = []
        for i, result in enumerate(updated_papers):
            if isinstance(result, Exception):
                self.logger.error(f"Download task failed for paper {i}: {result}")
                valid_papers.append(papers[i])  # Return original paper data
            else:
                valid_papers.append(result)
        
        self.logger.info(f"Batch download completed: {self.stats}")
        return valid_papers
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get download statistics."""
        stats = self.stats.copy()
        stats["success_rate"] = (
            (stats["successful"] / stats["attempted"]) * 100 
            if stats["attempted"] > 0 else 0
        )
        stats["total_size_mb"] = round(stats["bytes_downloaded"] / (1024 * 1024), 2)
        return stats
    
    def reset_stats(self):
        """Reset download statistics."""
        self.stats = {
            "attempted": 0,
            "successful": 0,
            "failed": 0,
            "skipped_storage": 0,
            "bytes_downloaded": 0
        }


# Convenience functions
async def download_arxiv_pdfs(papers: List[Dict[str, Any]], 
                             storage_path: str = "papers",
                             max_concurrent: int = 2) -> List[Dict[str, Any]]:
    """
    Convenience function to download arXiv PDFs.
    
    Args:
        papers: List of paper metadata
        storage_path: Base path for storing files
        max_concurrent: Maximum concurrent downloads
        
    Returns:
        List of updated paper metadata
    """
    storage = StorageManager(storage_path)
    
    async with PDFDownloader(storage, rate_limit_delay=2.0) as downloader:
        return await downloader.download_papers_batch(papers, max_concurrent)