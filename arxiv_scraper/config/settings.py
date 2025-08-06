"""
Configuration settings for the arXiv Scraper Project

Contains database, storage, and system settings optimized for academic paper collection.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """MongoDB database configuration."""
    host: str = "localhost"
    port: int = 27017
    database_name: str = "arxiv_scraper"
    username: Optional[str] = None
    password: Optional[str] = None
    max_pool_size: int = 50
    min_pool_size: int = 10
    timeout_ms: int = 30000
    data_path: str = "/mnt/data/mongodb/data"
    log_path: str = "/mnt/data/mongodb/logs"


@dataclass
class StorageConfig:
    """Storage configuration for PDF files."""
    base_path: str = "/mnt/data/arxiv_papers"
    max_storage_gb: int = 300
    papers_subdir: str = "papers"
    books_subdir: str = "books" 
    articles_subdir: str = "articles"
    temp_dir: str = "temp"
    
    @property
    def papers_path(self) -> str:
        return os.path.join(self.base_path, self.papers_subdir)
    
    @property
    def books_path(self) -> str:
        return os.path.join(self.base_path, self.books_subdir)
        
    @property
    def articles_path(self) -> str:
        return os.path.join(self.base_path, self.articles_subdir)
        
    @property
    def temp_path(self) -> str:
        return os.path.join(self.base_path, self.temp_dir)


@dataclass
class ScrapingConfig:
    """Configuration for web scraping and API access."""
    arxiv_base_url: str = "http://export.arxiv.org/api/query"
    arxiv_rate_limit_seconds: float = 3.0
    max_concurrent_downloads: int = 5
    request_timeout_seconds: int = 30
    max_retries: int = 3
    user_agent: str = "arXiv-Scraper/1.0 (Academic Research)"


@dataclass
class ProcessingConfig:
    """Configuration for data processing and analysis."""
    batch_size: int = 100
    max_workers: int = 4
    enable_text_extraction: bool = True
    enable_nlp_preprocessing: bool = False
    log_level: str = "INFO"


class Settings:
    """Main settings class for the arXiv scraper project."""
    
    def __init__(self):
        """Initialize settings with environment variable overrides."""
        self.database = self._init_database_config()
        self.storage = self._init_storage_config()
        self.scraping = self._init_scraping_config()
        self.processing = self._init_processing_config()
        
    def _init_database_config(self) -> DatabaseConfig:
        """Initialize database configuration with environment overrides."""
        return DatabaseConfig(
            host=os.getenv("MONGODB_HOST", "localhost"),
            port=int(os.getenv("MONGODB_PORT", "27017")),
            database_name=os.getenv("MONGODB_DATABASE", "arxiv_scraper"),
            username=os.getenv("MONGODB_USERNAME"),
            password=os.getenv("MONGODB_PASSWORD"),
            max_pool_size=int(os.getenv("MONGODB_MAX_POOL_SIZE", "50")),
            min_pool_size=int(os.getenv("MONGODB_MIN_POOL_SIZE", "10")),
            timeout_ms=int(os.getenv("MONGODB_TIMEOUT_MS", "30000")),
            data_path=os.getenv("MONGODB_DATA_PATH", "/mnt/data/mongodb/data"),
            log_path=os.getenv("MONGODB_LOG_PATH", "/mnt/data/mongodb/logs"),
        )
        
    def _init_storage_config(self) -> StorageConfig:
        """Initialize storage configuration with environment overrides."""
        return StorageConfig(
            base_path=os.getenv("STORAGE_BASE_PATH", "/mnt/data/arxiv_papers"),
            max_storage_gb=int(os.getenv("MAX_STORAGE_GB", "300")),
            papers_subdir=os.getenv("PAPERS_SUBDIR", "papers"),
            books_subdir=os.getenv("BOOKS_SUBDIR", "books"),
            articles_subdir=os.getenv("ARTICLES_SUBDIR", "articles"),
            temp_dir=os.getenv("TEMP_DIR", "temp"),
        )
        
    def _init_scraping_config(self) -> ScrapingConfig:
        """Initialize scraping configuration with environment overrides."""
        return ScrapingConfig(
            arxiv_base_url=os.getenv("ARXIV_BASE_URL", "http://export.arxiv.org/api/query"),
            arxiv_rate_limit_seconds=float(os.getenv("ARXIV_RATE_LIMIT_SECONDS", "3.0")),
            max_concurrent_downloads=int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5")),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            user_agent=os.getenv("USER_AGENT", "arXiv-Scraper/1.0 (Academic Research)"),
        )
        
    def _init_processing_config(self) -> ProcessingConfig:
        """Initialize processing configuration with environment overrides."""
        return ProcessingConfig(
            batch_size=int(os.getenv("BATCH_SIZE", "100")),
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            enable_text_extraction=os.getenv("ENABLE_TEXT_EXTRACTION", "true").lower() == "true",
            enable_nlp_preprocessing=os.getenv("ENABLE_NLP_PREPROCESSING", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary format."""
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database_name": self.database.database_name,
                "max_pool_size": self.database.max_pool_size,
                "min_pool_size": self.database.min_pool_size,
                "timeout_ms": self.database.timeout_ms,
                "data_path": self.database.data_path,
                "log_path": self.database.log_path,
            },
            "storage": {
                "base_path": self.storage.base_path,
                "max_storage_gb": self.storage.max_storage_gb,
                "papers_path": self.storage.papers_path,
                "books_path": self.storage.books_path,
                "articles_path": self.storage.articles_path,
                "temp_path": self.storage.temp_path,
            },
            "scraping": {
                "arxiv_base_url": self.scraping.arxiv_base_url,
                "arxiv_rate_limit_seconds": self.scraping.arxiv_rate_limit_seconds,
                "max_concurrent_downloads": self.scraping.max_concurrent_downloads,
                "request_timeout_seconds": self.scraping.request_timeout_seconds,
                "max_retries": self.scraping.max_retries,
                "user_agent": self.scraping.user_agent,
            },
            "processing": {
                "batch_size": self.processing.batch_size,
                "max_workers": self.processing.max_workers,
                "enable_text_extraction": self.processing.enable_text_extraction,
                "enable_nlp_preprocessing": self.processing.enable_nlp_preprocessing,
                "log_level": self.processing.log_level,
            }
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """Reload settings from environment variables."""
    global _settings
    _settings = None
    return get_settings()