"""
MongoDB Operations for arXiv Scraper Project

Defines database schemas and operations for storing academic paper metadata
from multiple sources (arXiv, Project Gutenberg, journals, etc.).
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, BulkWriteError
from .mongodb_connector import MongoDBConnector, get_connector

logger = logging.getLogger(__name__)


class SchemaDefinitions:
    """Database schema definitions for different content types."""
    
    @staticmethod
    def get_paper_schema() -> Dict[str, Any]:
        """
        Schema for academic papers (arXiv, journals, etc.).
        
        Returns:
            Dictionary defining paper document structure
        """
        return {
            "paper_id": str,  # Unique identifier (arXiv ID, DOI, etc.)
            "source": str,    # Source type: "arxiv", "journal", "preprint"
            "title": str,     # Paper title
            "authors": List[str],  # List of author names
            "abstract": str,  # Paper abstract
            "categories": List[str],  # Subject categories
            "date_published": datetime,  # Publication date
            "date_updated": Optional[datetime],  # Last update date
            "pdf_url": str,   # URL to PDF file
            "pdf_downloaded": bool,  # Whether PDF has been downloaded
            "pdf_file_path": Optional[str],  # Local path to downloaded PDF
            "pdf_file_size": Optional[int],  # PDF file size in bytes
            "source_metadata": Dict[str, Any],  # Source-specific metadata
            "processing_status": str,  # Status: "pending", "processed", "error"
            "created_at": datetime,  # Record creation time
            "updated_at": datetime,  # Record update time
        }
    
    @staticmethod
    def get_book_schema() -> Dict[str, Any]:
        """
        Schema for books (Project Gutenberg, etc.).
        
        Returns:
            Dictionary defining book document structure
        """
        return {
            "book_id": str,   # Unique identifier (Gutenberg ID, ISBN, etc.)
            "source": str,    # Source type: "gutenberg", "archive_org"
            "title": str,     # Book title
            "authors": List[str],  # List of author names
            "abstract": Optional[str],  # Book description/summary
            "subjects": List[str],  # Book subjects/categories
            "language": str,  # Book language
            "date_published": Optional[datetime],  # Original publication date
            "formats": List[Dict[str, str]],  # Available formats and URLs
            "pdf_url": Optional[str],  # URL to PDF file
            "pdf_downloaded": bool,  # Whether PDF has been downloaded
            "pdf_file_path": Optional[str],  # Local path to downloaded PDF
            "pdf_file_size": Optional[int],  # PDF file size in bytes
            "source_metadata": Dict[str, Any],  # Source-specific metadata
            "processing_status": str,  # Status: "pending", "processed", "error"
            "created_at": datetime,  # Record creation time
            "updated_at": datetime,  # Record update time
        }
    
    @staticmethod
    def get_article_schema() -> Dict[str, Any]:
        """
        Schema for articles from various sources.
        
        Returns:
            Dictionary defining article document structure
        """
        return {
            "article_id": str,  # Unique identifier
            "source": str,    # Source type: "journal", "magazine", "blog"
            "title": str,     # Article title
            "authors": List[str],  # List of author names
            "abstract": Optional[str],  # Article abstract/summary
            "keywords": List[str],  # Article keywords
            "journal": Optional[str],  # Journal name
            "volume": Optional[str],  # Journal volume
            "issue": Optional[str],   # Journal issue
            "pages": Optional[str],   # Page numbers
            "doi": Optional[str],     # Digital Object Identifier
            "date_published": datetime,  # Publication date
            "pdf_url": Optional[str],  # URL to PDF file
            "web_url": Optional[str],  # URL to web version
            "pdf_downloaded": bool,  # Whether PDF has been downloaded
            "pdf_file_path": Optional[str],  # Local path to downloaded PDF
            "pdf_file_size": Optional[int],  # PDF file size in bytes
            "source_metadata": Dict[str, Any],  # Source-specific metadata
            "processing_status": str,  # Status: "pending", "processed", "error"
            "created_at": datetime,  # Record creation time
            "updated_at": datetime,  # Record update time
        }


class IndexDefinitions:
    """Database index definitions for optimal query performance."""
    
    @staticmethod
    def get_paper_indexes() -> List[IndexModel]:
        """Get index definitions for papers collection."""
        return [
            IndexModel([("paper_id", ASCENDING)], unique=True),
            IndexModel([("source", ASCENDING)]),
            IndexModel([("authors", ASCENDING)]),
            IndexModel([("categories", ASCENDING)]),
            IndexModel([("date_published", DESCENDING)]),
            IndexModel([("processing_status", ASCENDING)]),
            IndexModel([("pdf_downloaded", ASCENDING)]),
            IndexModel([("title", TEXT), ("abstract", TEXT)], name="text_search"),
            IndexModel([("created_at", DESCENDING)]),
        ]
    
    @staticmethod
    def get_book_indexes() -> List[IndexModel]:
        """Get index definitions for books collection."""
        return [
            IndexModel([("book_id", ASCENDING)], unique=True),
            IndexModel([("source", ASCENDING)]),
            IndexModel([("authors", ASCENDING)]),
            IndexModel([("subjects", ASCENDING)]),
            IndexModel([("language", ASCENDING)]),
            IndexModel([("processing_status", ASCENDING)]),
            IndexModel([("pdf_downloaded", ASCENDING)]),
            IndexModel([("title", TEXT), ("abstract", TEXT)], name="text_search"),
            IndexModel([("created_at", DESCENDING)]),
        ]
    
    @staticmethod
    def get_article_indexes() -> List[IndexModel]:
        """Get index definitions for articles collection."""
        return [
            IndexModel([("article_id", ASCENDING)], unique=True),
            IndexModel([("source", ASCENDING)]),
            IndexModel([("authors", ASCENDING)]),
            IndexModel([("journal", ASCENDING)]),
            IndexModel([("doi", ASCENDING)], sparse=True),
            IndexModel([("date_published", DESCENDING)]),
            IndexModel([("processing_status", ASCENDING)]),
            IndexModel([("pdf_downloaded", ASCENDING)]),
            IndexModel([("title", TEXT), ("abstract", TEXT), ("keywords", TEXT)], name="text_search"),
            IndexModel([("created_at", DESCENDING)]),
        ]


class MongoDBOperations:
    """High-level MongoDB operations for the arXiv scraper project."""
    
    def __init__(self, connector: Optional[MongoDBConnector] = None):
        """
        Initialize MongoDB operations.
        
        Args:
            connector: MongoDB connector instance (optional)
        """
        self.connector = connector or get_connector()
        self.database = None
        
        # Collection names
        self.PAPERS_COLLECTION = "papers"
        self.BOOKS_COLLECTION = "books"
        self.ARTICLES_COLLECTION = "articles"
        self.METADATA_COLLECTION = "metadata"
        
    def initialize_database(self) -> bool:
        """
        Initialize the database with collections and indexes.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Connect to database
            self.database = self.connector.connect()
            
            # Create collections and indexes
            self._create_collections_and_indexes()
            
            # Create metadata collection for tracking
            self._initialize_metadata_collection()
            
            logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def _create_collections_and_indexes(self):
        """Create collections and their indexes."""
        # Papers collection
        papers_indexes = IndexDefinitions.get_paper_indexes()
        self.connector.create_indexes(self.PAPERS_COLLECTION, papers_indexes)
        logger.info(f"Created indexes for {self.PAPERS_COLLECTION} collection")
        
        # Books collection
        books_indexes = IndexDefinitions.get_book_indexes()
        self.connector.create_indexes(self.BOOKS_COLLECTION, books_indexes)
        logger.info(f"Created indexes for {self.BOOKS_COLLECTION} collection")
        
        # Articles collection
        articles_indexes = IndexDefinitions.get_article_indexes()
        self.connector.create_indexes(self.ARTICLES_COLLECTION, articles_indexes)
        logger.info(f"Created indexes for {self.ARTICLES_COLLECTION} collection")
        
    def _initialize_metadata_collection(self):
        """Initialize metadata collection for tracking system information."""
        metadata_collection = self.connector.get_collection(self.METADATA_COLLECTION)
        
        # Insert initial metadata if not exists
        metadata_doc = {
            "system_info": {
                "database_version": "1.0",
                "created_at": datetime.utcnow(),
                "storage_location": "/mnt/data/mongodb",
                "max_storage_gb": 300,
            },
            "collections": {
                "papers": {"schema_version": "1.0"},
                "books": {"schema_version": "1.0"},
                "articles": {"schema_version": "1.0"},
            },
            "updated_at": datetime.utcnow()
        }
        
        metadata_collection.replace_one(
            {"_id": "system_metadata"},
            {**metadata_doc, "_id": "system_metadata"},
            upsert=True
        )
    
    def insert_paper(self, paper_data: Dict[str, Any]) -> bool:
        """
        Insert a paper document.
        
        Args:
            paper_data: Paper metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            paper_data.update({
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "processing_status": paper_data.get("processing_status", "pending"),
                "pdf_downloaded": paper_data.get("pdf_downloaded", False),
            })
            
            collection = self.connector.get_collection(self.PAPERS_COLLECTION)
            collection.insert_one(paper_data)
            
            logger.debug(f"Inserted paper: {paper_data.get('paper_id')}")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Paper already exists: {paper_data.get('paper_id')}")
            return False
        except Exception as e:
            logger.error(f"Failed to insert paper: {e}")
            return False
    
    def bulk_insert_papers(self, papers_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk insert paper documents.
        
        Args:
            papers_data: List of paper metadata dictionaries
            
        Returns:
            Dictionary with insertion statistics
        """
        if not papers_data:
            return {"inserted": 0, "errors": 0}
        
        # Add timestamps and default values
        current_time = datetime.utcnow()
        for paper in papers_data:
            paper.update({
                "created_at": current_time,
                "updated_at": current_time,
                "processing_status": paper.get("processing_status", "pending"),
                "pdf_downloaded": paper.get("pdf_downloaded", False),
            })
        
        collection = self.connector.get_collection(self.PAPERS_COLLECTION)
        
        try:
            result = collection.insert_many(papers_data, ordered=False)
            inserted_count = len(result.inserted_ids)
            
            logger.info(f"Bulk inserted {inserted_count} papers")
            return {"inserted": inserted_count, "errors": 0}
            
        except BulkWriteError as e:
            inserted_count = e.details.get("nInserted", 0)
            error_count = len(e.details.get("writeErrors", []))
            
            logger.warning(f"Bulk insert completed with {inserted_count} inserted, {error_count} errors")
            return {"inserted": inserted_count, "errors": error_count}
        
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            return {"inserted": 0, "errors": len(papers_data)}
    
    def find_papers(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find papers matching query.
        
        Args:
            query: MongoDB query dictionary
            limit: Maximum number of results
            
        Returns:
            List of paper documents
        """
        collection = self.connector.get_collection(self.PAPERS_COLLECTION)
        cursor = collection.find(query).limit(limit)
        return list(cursor)
    
    def update_paper_download_status(self, paper_id: str, file_path: str, file_size: int) -> bool:
        """
        Update paper download status.
        
        Args:
            paper_id: Paper identifier
            file_path: Path to downloaded PDF
            file_size: File size in bytes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.connector.get_collection(self.PAPERS_COLLECTION)
            result = collection.update_one(
                {"paper_id": paper_id},
                {
                    "$set": {
                        "pdf_downloaded": True,
                        "pdf_file_path": file_path,
                        "pdf_file_size": file_size,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update download status for {paper_id}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all collections.
        
        Returns:
            Dictionary containing collection statistics
        """
        stats = {}
        collections = [self.PAPERS_COLLECTION, self.BOOKS_COLLECTION, self.ARTICLES_COLLECTION]
        
        for collection_name in collections:
            collection = self.connector.get_collection(collection_name)
            stats[collection_name] = {
                "document_count": collection.count_documents({}),
                "downloaded_count": collection.count_documents({"pdf_downloaded": True}),
                "pending_count": collection.count_documents({"processing_status": "pending"}),
            }
        
        return stats
    
    def search_text(self, search_term: str, collection_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Perform text search across collections.
        
        Args:
            search_term: Text to search for
            collection_name: Specific collection to search (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        results = []
        collections = [collection_name] if collection_name else [
            self.PAPERS_COLLECTION, self.BOOKS_COLLECTION, self.ARTICLES_COLLECTION
        ]
        
        for coll_name in collections:
            collection = self.connector.get_collection(coll_name)
            cursor = collection.find(
                {"$text": {"$search": search_term}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            for doc in cursor:
                doc["_collection"] = coll_name
                results.append(doc)
        
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:limit]


# Global operations instance
_operations: Optional[MongoDBOperations] = None


def get_operations() -> MongoDBOperations:
    """Get global MongoDB operations instance."""
    global _operations
    if _operations is None:
        _operations = MongoDBOperations()
    return _operations