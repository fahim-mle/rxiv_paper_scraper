"""
Enhanced Downloader Agent with MCP Server integration.
Uses Fetch MCP for PDF downloads with rate limiting and storage management.
"""

import asyncio
import logging
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import aiofiles

from .mcp_servers.client_manager import mcp_manager
from .utils.logger import get_logger
from .utils.rate_limiter import RateLimiter


@dataclass
class DownloadResult:
    url: str
    local_path: Optional[str]
    success: bool
    file_size: int = 0
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    download_time: float = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class StorageStats:
    total_files: int
    total_size_gb: float
    available_space_gb: float
    storage_limit_gb: float = 300.0
    usage_percentage: float = 0.0
    
    def __post_init__(self):
        self.usage_percentage = (self.total_size_gb / self.storage_limit_gb) * 100


class MCPEnhancedDownloaderAgent:
    def __init__(self, storage_path: str = "./papers"):
        self.logger = get_logger(__name__)
        self.storage_path = Path(storage_path)
        self.storage_limit_gb = 300.0
        self.rate_limiter = RateLimiter(delay=1.0)  # 1 second between downloads
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Download tracking
        self.active_downloads = set()
        self.download_history = []
        
    async def initialize(self) -> bool:
        """Initialize MCP connections required for downloading."""
        connection_result = await mcp_manager.connect_server("fetch")
        
        if connection_result:
            self.logger.info("Connected to Fetch MCP server for downloads")
            return True
        else:
            self.logger.warning("Fetch MCP server not available, using fallback downloader")
            return False
    
    async def download_pdf(self, url: str, paper_id: str = None, 
                          verify_integrity: bool = True) -> DownloadResult:
        """
        Download a single PDF file.
        
        Args:
            url: PDF URL to download
            paper_id: Unique identifier for the paper
            verify_integrity: Whether to verify file integrity
        """
        if url in self.active_downloads:
            return DownloadResult(
                url=url,
                local_path=None,
                success=False,
                error_message="Download already in progress"
            )
        
        # Check storage limits
        if not await self._check_storage_capacity():
            return DownloadResult(
                url=url,
                local_path=None,
                success=False,
                error_message="Storage limit exceeded"
            )
        
        self.active_downloads.add(url)
        start_time = asyncio.get_event_loop().time()
        
        try:
            await self.rate_limiter.wait()
            
            # Generate local filename
            local_path = self._generate_local_path(url, paper_id)
            
            # Check if file already exists
            if local_path.exists():
                self.logger.info(f"File already exists: {local_path}")
                result = DownloadResult(
                    url=url,
                    local_path=str(local_path),
                    success=True,
                    file_size=local_path.stat().st_size,
                    checksum=await self._calculate_checksum(local_path) if verify_integrity else None,
                    download_time=0
                )
                return result
            
            # Download using MCP server if available
            if mcp_manager.is_server_connected("fetch"):
                result = await self._download_with_mcp(url, local_path, verify_integrity)
            else:
                result = await self._download_fallback(url, local_path, verify_integrity)
            
            result.download_time = asyncio.get_event_loop().time() - start_time
            self.download_history.append(result)
            
            if result.success:
                self.logger.info(f"Downloaded PDF: {url} -> {result.local_path} ({result.file_size} bytes)")
            
            return result
            
        except Exception as e:
            error_msg = f"Download failed for {url}: {str(e)}"
            self.logger.error(error_msg)
            return DownloadResult(
                url=url,
                local_path=None,
                success=False,
                error_message=error_msg,
                download_time=asyncio.get_event_loop().time() - start_time
            )
            
        finally:
            self.active_downloads.discard(url)
    
    async def download_batch(self, pdf_urls: List[str], 
                           max_concurrent: int = 5) -> List[DownloadResult]:
        """
        Download multiple PDFs concurrently.
        
        Args:
            pdf_urls: List of PDF URLs to download
            max_concurrent: Maximum concurrent downloads
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(url):
            async with semaphore:
                return await self.download_pdf(url)
        
        self.logger.info(f"Starting batch download of {len(pdf_urls)} PDFs")
        
        tasks = [download_with_semaphore(url) for url in pdf_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        download_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                download_results.append(DownloadResult(
                    url=pdf_urls[i],
                    local_path=None,
                    success=False,
                    error_message=str(result)
                ))
            else:
                download_results.append(result)
        
        successful = sum(1 for r in download_results if r.success)
        self.logger.info(f"Batch download completed: {successful}/{len(pdf_urls)} successful")
        
        return download_results
    
    async def manage_storage(self, cleanup_threshold: float = 0.95) -> Dict[str, Any]:
        """
        Manage storage space by cleaning up old/duplicate files.
        
        Args:
            cleanup_threshold: Storage usage percentage to trigger cleanup
            
        Returns:
            Storage management report
        """
        stats = await self.get_storage_stats()
        
        if stats.usage_percentage < cleanup_threshold * 100:
            return {
                "cleanup_needed": False,
                "current_usage": stats.usage_percentage,
                "threshold": cleanup_threshold * 100
            }
        
        self.logger.info(f"Storage cleanup needed: {stats.usage_percentage:.1f}% used")
        
        # Find duplicate files
        duplicates = await self._find_duplicate_files()
        
        # Find old files (oldest 10%)
        old_files = await self._find_old_files(percentage=0.1)
        
        # Remove duplicates first
        removed_duplicates = 0
        freed_space = 0
        
        for dup_group in duplicates:
            # Keep the first file, remove others
            for file_path in dup_group[1:]:
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    removed_duplicates += 1
                    freed_space += size
                    self.logger.info(f"Removed duplicate: {file_path}")
                except Exception as e:
                    self.logger.error(f"Failed to remove duplicate {file_path}: {e}")
        
        # Remove old files if still needed
        removed_old = 0
        stats = await self.get_storage_stats()
        
        if stats.usage_percentage >= cleanup_threshold * 100:
            for file_path in old_files:
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    removed_old += 1
                    freed_space += size
                    self.logger.info(f"Removed old file: {file_path}")
                    
                    # Check if we've freed enough space
                    stats = await self.get_storage_stats()
                    if stats.usage_percentage < cleanup_threshold * 100:
                        break
                        
                except Exception as e:
                    self.logger.error(f"Failed to remove old file {file_path}: {e}")
        
        final_stats = await self.get_storage_stats()
        
        return {
            "cleanup_needed": True,
            "removed_duplicates": removed_duplicates,
            "removed_old_files": removed_old,
            "freed_space_gb": freed_space / (1024**3),
            "final_usage_percentage": final_stats.usage_percentage
        }
    
    async def verify_integrity(self, file_path: Path, 
                             expected_checksum: str = None) -> bool:
        """
        Verify file integrity.
        
        Args:
            file_path: Path to file to verify
            expected_checksum: Expected checksum (if available)
        """
        try:
            if not file_path.exists():
                return False
            
            if file_path.stat().st_size == 0:
                return False
            
            # Calculate checksum
            checksum = await self._calculate_checksum(file_path)
            
            if expected_checksum:
                return checksum == expected_checksum
            
            # Basic integrity check - ensure it's a valid PDF
            return await self._is_valid_pdf(file_path)
            
        except Exception as e:
            self.logger.error(f"Integrity verification failed for {file_path}: {e}")
            return False
    
    async def get_storage_stats(self) -> StorageStats:
        """Get current storage statistics."""
        total_size = 0
        total_files = 0
        
        for file_path in self.storage_path.rglob("*.pdf"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        total_size_gb = total_size / (1024**3)
        
        # Calculate available space
        statvfs = os.statvfs(self.storage_path)
        available_space_gb = (statvfs.f_bavail * statvfs.f_frsize) / (1024**3)
        
        return StorageStats(
            total_files=total_files,
            total_size_gb=total_size_gb,
            available_space_gb=available_space_gb
        )
    
    async def _download_with_mcp(self, url: str, local_path: Path, 
                               verify_integrity: bool) -> DownloadResult:
        """Download using Fetch MCP server."""
        try:
            response = await mcp_manager.call_tool(
                "fetch",
                "fetch_url",
                {
                    "url": url,
                    "save_to_file": str(local_path),
                    "timeout": 60
                }
            )
            
            if response.get("success"):
                file_size = local_path.stat().st_size if local_path.exists() else 0
                checksum = await self._calculate_checksum(local_path) if verify_integrity else None
                
                return DownloadResult(
                    url=url,
                    local_path=str(local_path),
                    success=True,
                    file_size=file_size,
                    checksum=checksum
                )
            else:
                error_msg = response.get("error", "Unknown MCP download error")
                return DownloadResult(
                    url=url,
                    local_path=None,
                    success=False,
                    error_message=error_msg
                )
                
        except Exception as e:
            return DownloadResult(
                url=url,
                local_path=None,
                success=False,
                error_message=f"MCP download failed: {str(e)}"
            )
    
    async def _download_fallback(self, url: str, local_path: Path, 
                               verify_integrity: bool) -> DownloadResult:
        """Fallback download using aiohttp."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        async with aiofiles.open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        file_size = local_path.stat().st_size
                        checksum = await self._calculate_checksum(local_path) if verify_integrity else None
                        
                        return DownloadResult(
                            url=url,
                            local_path=str(local_path),
                            success=True,
                            file_size=file_size,
                            checksum=checksum
                        )
                    else:
                        return DownloadResult(
                            url=url,
                            local_path=None,
                            success=False,
                            error_message=f"HTTP {response.status}: {response.reason}"
                        )
                        
        except Exception as e:
            return DownloadResult(
                url=url,
                local_path=None,
                success=False,
                error_message=f"Fallback download failed: {str(e)}"
            )
    
    def _generate_local_path(self, url: str, paper_id: str = None) -> Path:
        """Generate local file path for download."""
        if paper_id:
            filename = f"{paper_id}.pdf"
        else:
            # Extract filename from URL or generate from hash
            filename = url.split('/')[-1]
            if not filename.endswith('.pdf'):
                url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
                filename = f"{url_hash}.pdf"
        
        # Create subdirectory based on first character for organization
        subdir = filename[0].lower()
        if not subdir.isalnum():
            subdir = "other"
        
        return self.storage_path / subdir / filename
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file."""
        hash_md5 = hashlib.md5()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    async def _is_valid_pdf(self, file_path: Path) -> bool:
        """Basic PDF validation."""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                header = await f.read(4)
                return header == b'%PDF'
        except:
            return False
    
    async def _check_storage_capacity(self) -> bool:
        """Check if storage has capacity for new downloads."""
        stats = await self.get_storage_stats()
        return stats.usage_percentage < 95.0  # Leave 5% buffer
    
    async def _find_duplicate_files(self) -> List[List[Path]]:
        """Find duplicate files by checksum."""
        checksum_map = {}
        
        for file_path in self.storage_path.rglob("*.pdf"):
            if file_path.is_file():
                try:
                    checksum = await self._calculate_checksum(file_path)
                    if checksum in checksum_map:
                        checksum_map[checksum].append(file_path)
                    else:
                        checksum_map[checksum] = [file_path]
                except Exception as e:
                    self.logger.error(f"Checksum calculation failed for {file_path}: {e}")
        
        # Return groups with more than one file
        return [files for files in checksum_map.values() if len(files) > 1]
    
    async def _find_old_files(self, percentage: float) -> List[Path]:
        """Find oldest files by modification time."""
        files_with_mtime = []
        
        for file_path in self.storage_path.rglob("*.pdf"):
            if file_path.is_file():
                mtime = file_path.stat().st_mtime
                files_with_mtime.append((mtime, file_path))
        
        # Sort by modification time (oldest first)
        files_with_mtime.sort(key=lambda x: x[0])
        
        # Return oldest percentage of files
        count = int(len(files_with_mtime) * percentage)
        return [file_path for _, file_path in files_with_mtime[:count]]
    
    async def get_download_stats(self) -> Dict[str, Any]:
        """Get download statistics."""
        successful = sum(1 for r in self.download_history if r.success)
        failed = len(self.download_history) - successful
        
        if self.download_history:
            avg_size = sum(r.file_size for r in self.download_history if r.success) / max(successful, 1)
            avg_time = sum(r.download_time for r in self.download_history) / len(self.download_history)
        else:
            avg_size = 0
            avg_time = 0
        
        return {
            "total_downloads": len(self.download_history),
            "successful_downloads": successful,
            "failed_downloads": failed,
            "success_rate": successful / max(len(self.download_history), 1) * 100,
            "average_file_size_mb": avg_size / (1024**2),
            "average_download_time": avg_time,
            "active_downloads": len(self.active_downloads)
        }
    
    async def shutdown(self):
        """Clean shutdown of downloader agent."""
        self.logger.info("Shutting down Enhanced Downloader Agent")
        # Wait for active downloads to complete
        while self.active_downloads:
            await asyncio.sleep(1)