"""
MongoDB Connector for arXiv Scraper Project

Handles database connections, connection pooling, and basic operations
optimized for academic paper metadata storage.
"""

import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, IndexModel
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from urllib.parse import quote_plus
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class MongoDBConnector:
    """MongoDB connection manager for the arXiv scraper project."""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 27017,
                 database_name: str = "arxiv_scraper",
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 max_pool_size: int = 50,
                 min_pool_size: int = 10,
                 timeout_ms: int = 30000):
        """
        Initialize MongoDB connector.
        
        Args:
            host: MongoDB host address
            port: MongoDB port
            database_name: Name of the database
            username: MongoDB username (optional)
            password: MongoDB password (optional)
            max_pool_size: Maximum connection pool size
            min_pool_size: Minimum connection pool size
            timeout_ms: Connection timeout in milliseconds
        """
        self.host = host
        self.port = port
        self.database_name = database_name
        self.username = username
        self.password = password
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.timeout_ms = timeout_ms
        
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
        self._async_client: Optional[AsyncIOMotorClient] = None
        
    def _build_connection_string(self) -> str:
        """Build MongoDB connection string."""
        if self.username and self.password:
            auth_string = f"{quote_plus(self.username)}:{quote_plus(self.password)}@"
        else:
            auth_string = ""
            
        connection_string = (
            f"mongodb://{auth_string}{self.host}:{self.port}/{self.database_name}"
            f"?maxPoolSize={self.max_pool_size}"
            f"&minPoolSize={self.min_pool_size}"
            f"&serverSelectionTimeoutMS={self.timeout_ms}"
            f"&retryWrites=true"
            f"&w=majority"
        )
        return connection_string
    
    def connect(self) -> Database:
        """
        Establish connection to MongoDB and return database instance.
        
        Returns:
            Database instance
            
        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        if self._client is None:
            try:
                connection_string = self._build_connection_string()
                self._client = MongoClient(connection_string)
                
                # Test the connection
                self._client.admin.command('ping')
                self._database = self._client[self.database_name]
                
                logger.info(f"Successfully connected to MongoDB: {self.host}:{self.port}")
                logger.info(f"Database: {self.database_name}")
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise ConnectionFailure(f"Cannot connect to MongoDB at {self.host}:{self.port}")
        
        return self._database
    
    def get_async_client(self) -> AsyncIOMotorClient:
        """
        Get async MongoDB client for concurrent operations.
        
        Returns:
            AsyncIOMotorClient instance
        """
        if self._async_client is None:
            connection_string = self._build_connection_string()
            self._async_client = AsyncIOMotorClient(connection_string)
            
        return self._async_client
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a specific collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection instance
        """
        if self._database is None:
            self.connect()
            
        return self._database[collection_name]
    
    def test_connection(self) -> bool:
        """
        Test MongoDB connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if self._client is None:
                self.connect()
            
            # Ping the server
            self._client.admin.command('ping')
            logger.info("MongoDB connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {e}")
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get MongoDB server information.
        
        Returns:
            Dictionary containing server information
        """
        if self._database is None:
            self.connect()
            
        return self._client.server_info()
    
    def list_collections(self) -> List[str]:
        """
        List all collections in the database.
        
        Returns:
            List of collection names
        """
        if self._database is None:
            self.connect()
            
        return self._database.list_collection_names()
    
    def create_indexes(self, collection_name: str, indexes: List[IndexModel]) -> List[str]:
        """
        Create indexes on a collection.
        
        Args:
            collection_name: Name of the collection
            indexes: List of IndexModel objects
            
        Returns:
            List of created index names
        """
        collection = self.get_collection(collection_name)
        return collection.create_indexes(indexes)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary containing database statistics
        """
        if self._database is None:
            self.connect()
            
        return self._database.command("dbStats")
    
    def close(self):
        """Close MongoDB connections."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")
            
        if self._async_client:
            self._async_client.close()
            self._async_client = None


# Global connector instance
_connector: Optional[MongoDBConnector] = None


def get_connector(username: Optional[str] = None, password: Optional[str] = None) -> MongoDBConnector:
    """
    Get global MongoDB connector instance.
    
    Args:
        username: MongoDB username (optional)
        password: MongoDB password (optional)
        
    Returns:
        MongoDBConnector instance
    """
    global _connector
    
    if _connector is None:
        # Try to get credentials from environment variables
        env_username = os.getenv('MONGODB_USERNAME', username)
        env_password = os.getenv('MONGODB_PASSWORD', password)
        
        _connector = MongoDBConnector(
            username=env_username,
            password=env_password
        )
    
    return _connector


def close_global_connector():
    """Close the global connector."""
    global _connector
    if _connector:
        _connector.close()
        _connector = None