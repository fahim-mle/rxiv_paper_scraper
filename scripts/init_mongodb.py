#!/usr/bin/env python3
"""
MongoDB Initialization Script for arXiv Scraper Project

This script initializes the MongoDB database with proper collections,
indexes, and user authentication for the multi-agent scraper system.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from arxiv_scraper.database.mongodb_connector import get_connector
from arxiv_scraper.database.mongodb_operations import get_operations
from arxiv_scraper.config.settings import get_settings


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/tmp/mongodb_init.log')
        ]
    )


def create_storage_directories():
    """Create necessary storage directories."""
    settings = get_settings()
    
    directories = [
        settings.storage.base_path,
        settings.storage.papers_path,
        settings.storage.books_path,
        settings.storage.articles_path,
        settings.storage.temp_path,
        settings.database.data_path,
        settings.database.log_path,
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Created/verified directory: {directory}")
        except Exception as e:
            logging.error(f"Failed to create directory {directory}: {e}")
            return False
    
    return True


def test_mongodb_connection():
    """Test MongoDB connection."""
    logging.info("Testing MongoDB connection...")
    
    try:
        connector = get_connector()
        
        if not connector.test_connection():
            logging.error("MongoDB connection test failed")
            return False
        
        # Get server info
        server_info = connector.get_server_info()
        logging.info(f"Connected to MongoDB {server_info.get('version')}")
        
        return True
        
    except Exception as e:
        logging.error(f"MongoDB connection error: {e}")
        return False


def initialize_database():
    """Initialize database collections and indexes."""
    logging.info("Initializing database structure...")
    
    try:
        operations = get_operations()
        
        if not operations.initialize_database():
            logging.error("Database initialization failed")
            return False
        
        # Get collection stats
        stats = operations.get_collection_stats()
        for collection, stat in stats.items():
            logging.info(f"Collection {collection}: {stat['document_count']} documents")
        
        return True
        
    except Exception as e:
        logging.error(f"Database initialization error: {e}")
        return False


def create_admin_user():
    """Create admin user for MongoDB."""
    logging.info("Setting up MongoDB admin user...")
    
    try:
        connector = get_connector()
        database = connector.connect()
        
        # Check if admin user already exists
        admin_db = connector._client.admin
        users = admin_db.command("usersInfo")["users"]
        
        admin_exists = any(user["user"] == "arxiv_admin" for user in users)
        
        if admin_exists:
            logging.info("Admin user already exists")
            return True
        
        # Create admin user
        admin_password = os.getenv("MONGODB_ADMIN_PASSWORD", "admin_password_change_me")
        
        admin_db.command("createUser", "arxiv_admin", pwd=admin_password, roles=[
            {"role": "readWrite", "db": "arxiv_scraper"},
            {"role": "dbAdmin", "db": "arxiv_scraper"}
        ])
        
        logging.info("Created admin user: arxiv_admin")
        logging.warning("Please change the default admin password!")
        
        return True
        
    except Exception as e:
        logging.error(f"Admin user creation error: {e}")
        return False


def create_app_user():
    """Create application user for MongoDB."""
    logging.info("Setting up MongoDB application user...")
    
    try:
        connector = get_connector()
        database = connector.connect()
        
        # Check if app user already exists
        users = database.command("usersInfo")["users"]
        app_exists = any(user["user"] == "arxiv_app" for user in users)
        
        if app_exists:
            logging.info("Application user already exists")
            return True
        
        # Create app user
        app_password = os.getenv("MONGODB_APP_PASSWORD", "app_password_change_me")
        
        database.command("createUser", "arxiv_app", pwd=app_password, roles=[
            {"role": "readWrite", "db": "arxiv_scraper"}
        ])
        
        logging.info("Created application user: arxiv_app")
        logging.warning("Please change the default application password!")
        
        return True
        
    except Exception as e:
        logging.error(f"Application user creation error: {e}")
        return False


def print_configuration_summary():
    """Print configuration summary."""
    settings = get_settings()
    
    print("\n" + "="*60)
    print("MongoDB Configuration Summary")
    print("="*60)
    print(f"Database Host: {settings.database.host}:{settings.database.port}")
    print(f"Database Name: {settings.database.database_name}")
    print(f"Data Directory: {settings.database.data_path}")
    print(f"Log Directory: {settings.database.log_path}")
    print(f"Storage Directory: {settings.storage.base_path}")
    print(f"Max Storage: {settings.storage.max_storage_gb} GB")
    print(f"Connection Pool: {settings.database.min_pool_size}-{settings.database.max_pool_size}")
    print("="*60)
    
    print("\nUsers Created:")
    print("- arxiv_admin: Database administrator")
    print("- arxiv_app: Application user")
    
    print("\nCollections Created:")
    print("- papers: arXiv papers and journal articles")
    print("- books: Project Gutenberg and other books")
    print("- articles: Articles from various sources")
    print("- metadata: System metadata and tracking")
    
    print("\nNext Steps:")
    print("1. Change default passwords in environment variables:")
    print("   export MONGODB_ADMIN_PASSWORD='your_secure_admin_password'")
    print("   export MONGODB_APP_PASSWORD='your_secure_app_password'")
    print("2. Start the scraper: python main.py")
    print("3. Monitor with: mongosh --eval 'db.stats()'")
    print("="*60)


def main():
    """Main initialization function."""
    setup_logging()
    
    logging.info("Starting MongoDB initialization for arXiv Scraper Project")
    
    # Step 1: Create storage directories
    if not create_storage_directories():
        logging.error("Failed to create storage directories")
        sys.exit(1)
    
    # Step 2: Test MongoDB connection
    if not test_mongodb_connection():
        logging.error("MongoDB connection failed")
        logging.error("Please ensure MongoDB is installed and running")
        logging.error("Use: sudo systemctl start mongod")
        sys.exit(1)
    
    # Step 3: Initialize database
    if not initialize_database():
        logging.error("Database initialization failed")
        sys.exit(1)
    
    # Step 4: Create users (if authentication is enabled)
    auth_enabled = os.getenv("MONGODB_AUTH_ENABLED", "false").lower() == "true"
    if auth_enabled:
        if not create_admin_user():
            logging.warning("Admin user creation failed")
        
        if not create_app_user():
            logging.warning("Application user creation failed")
    else:
        logging.info("Authentication disabled - skipping user creation")
    
    # Step 5: Print summary
    print_configuration_summary()
    
    logging.info("MongoDB initialization completed successfully")


if __name__ == "__main__":
    main()