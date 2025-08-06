#!/usr/bin/env python3
"""
MongoDB Setup Guide and Examples for arXiv Scraper Project

Provides step-by-step setup instructions and usage examples for agents.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_setup_instructions():
    """Print complete setup instructions."""
    print("""
MongoDB Setup Guide for arXiv Scraper Project
=============================================

This guide will help you set up MongoDB for the arXiv scraper project with
optimized configuration for academic paper storage and multi-agent access.

STEP 1: System-Level Setup (requires sudo)
-------------------------------------------

Run the system setup script to configure MongoDB on /mnt/data:

    cd /mnt/projects/workspace/rxiv_paper_scraper
    sudo ./scripts/setup_mongodb_system.sh

This script will:
- Create MongoDB data and log directories on /mnt/data
- Install optimized MongoDB configuration
- Set up proper file permissions
- Start MongoDB service
- Verify the installation

STEP 2: Database Initialization
-------------------------------

Initialize the database structure and create collections:

    python scripts/init_mongodb.py

This script will:
- Create database collections (papers, books, articles, metadata)
- Set up indexes for optimal query performance
- Initialize system metadata
- Create user accounts (if authentication is enabled)

STEP 3: Environment Configuration
---------------------------------

Copy and configure the environment file:

    cp .env.example .env

Edit .env and set secure passwords:

    # Required: Set secure passwords
    MONGODB_USERNAME=arxiv_app
    MONGODB_PASSWORD=your_secure_app_password
    MONGODB_ADMIN_PASSWORD=your_secure_admin_password
    
    # Optional: Adjust based on your system
    MONGODB_AUTH_ENABLED=true
    MAX_STORAGE_GB=300
    BATCH_SIZE=100

STEP 4: Verify Installation
--------------------------

Test the database connection and performance:

    python scripts/db_health_check.py
    python scripts/optimize_mongodb.py

STEP 5: Start Using the Database
--------------------------------

Import the database modules in your agents:

    from arxiv_scraper.database.mongodb_operations import get_operations
    from arxiv_scraper.database.agent_pool_manager import register_agent, get_agent_connection
    
    # Register your agent
    register_agent("my_agent_001", "crawler")
    
    # Use database connection
    with get_agent_connection("my_agent_001") as db:
        # Your database operations here
        pass

System Requirements:
===================
- Ubuntu 24.04 LTS (current system)
- MongoDB 8.0.12 (already installed)
- Python 3.8+ with required packages
- At least 4GB RAM (8GB+ recommended)
- 458GB available storage on /mnt/data

Troubleshooting:
===============
- Check logs: sudo journalctl -u mongod -f
- Verify service: sudo systemctl status mongod
- Check connection: mongosh --eval "db.adminCommand('ping')"
- Monitor health: python scripts/db_health_check.py --json

For more help, see the individual script documentation.
""")


def print_agent_usage_examples():
    """Print usage examples for different agent types."""
    print("""
Agent Usage Examples
===================

1. Crawler Agent Example:
------------------------

from arxiv_scraper.database.mongodb_operations import get_operations
from arxiv_scraper.database.agent_pool_manager import register_agent, get_agent_connection

# Register the crawler agent
register_agent("crawler_001", "crawler")

# Store discovered papers
operations = get_operations()

paper_data = {
    "paper_id": "2301.00001",
    "source": "arxiv",
    "title": "Example Paper Title",
    "authors": ["Author One", "Author Two"],
    "abstract": "This is an example abstract...",
    "categories": ["cs.AI", "cs.LG"],
    "date_published": datetime.utcnow(),
    "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
    "source_metadata": {"arxiv_id": "2301.00001"}
}

# Insert single paper
operations.insert_paper(paper_data)

# Bulk insert multiple papers
papers_list = [paper_data1, paper_data2, paper_data3]
result = operations.bulk_insert_papers(papers_list)
print(f"Inserted {result['inserted']} papers")


2. Scraper Agent Example:
-------------------------

# Register the scraper agent
register_agent("scraper_001", "scraper")

# Find papers that need processing
with get_agent_connection("scraper_001") as db:
    papers_collection = db["papers"]
    
    # Find unprocessed papers
    unprocessed_papers = papers_collection.find({
        "processing_status": "pending"
    }).limit(50)
    
    for paper in unprocessed_papers:
        # Process the paper
        enhanced_metadata = process_paper_metadata(paper)
        
        # Update with enhanced metadata
        papers_collection.update_one(
            {"paper_id": paper["paper_id"]},
            {
                "$set": {
                    "processing_status": "processed",
                    "enhanced_metadata": enhanced_metadata,
                    "updated_at": datetime.utcnow()
                }
            }
        )


3. Downloader Agent Example:
----------------------------

# Register the downloader agent
register_agent("downloader_001", "downloader")

operations = get_operations()

# Find papers that need PDF download
papers_to_download = operations.find_papers({
    "pdf_downloaded": False,
    "processing_status": "processed"
}, limit=20)

for paper in papers_to_download:
    try:
        # Download PDF (implement your download logic)
        file_path, file_size = download_pdf(paper["pdf_url"], paper["paper_id"])
        
        # Update download status
        operations.update_paper_download_status(
            paper["paper_id"], 
            file_path, 
            file_size
        )
        
    except Exception as e:
        # Handle download errors
        with get_agent_connection("downloader_001") as db:
            db["papers"].update_one(
                {"paper_id": paper["paper_id"]},
                {"$set": {"download_error": str(e)}}
            )


4. NLP Agent Example:
--------------------

# Register the NLP agent
register_agent("nlp_001", "nlp")

# Search papers by text
operations = get_operations()

# Text search across all collections
results = operations.search_text("machine learning transformers", limit=100)

# Process results for NLP pipeline
processed_papers = []
for result in results:
    if result.get("abstract"):
        # Extract features, embeddings, etc.
        nlp_features = extract_nlp_features(result["abstract"])
        result["nlp_features"] = nlp_features
        processed_papers.append(result)

# Export for training
export_data_for_training(processed_papers)


5. Monitoring Agent Example:
---------------------------

# Register monitoring agent
register_agent("monitor_001", "monitoring")

# Get system health
from arxiv_scraper.database.agent_pool_manager import get_agent_pool_manager

pool_manager = get_agent_pool_manager()
pool_status = pool_manager.get_pool_status()

print(f"Active connections: {pool_status['total_connections']}")
print(f"Registered agents: {pool_status['registered_agents']}")

# Get collection statistics
operations = get_operations()
stats = operations.get_collection_stats()

for collection, stat in stats.items():
    print(f"{collection}: {stat['document_count']} documents")
    print(f"  Downloaded: {stat['downloaded_count']}")
    print(f"  Pending: {stat['pending_count']}")


6. Batch Operations Example:
---------------------------

# For high-throughput operations
from pymongo import UpdateOne

batch_updates = []
for paper_id, new_status in status_updates:
    batch_updates.append(
        UpdateOne(
            {"paper_id": paper_id},
            {"$set": {"processing_status": new_status, "updated_at": datetime.utcnow()}}
        )
    )

# Execute batch update
with get_agent_connection("batch_processor_001") as db:
    result = db["papers"].bulk_write(batch_updates)
    print(f"Updated {result.modified_count} papers")


Best Practices:
==============

1. Always register your agent before using database connections
2. Use context managers (with statements) for database connections
3. Use bulk operations for high-throughput scenarios
4. Monitor connection usage with pool_manager.get_pool_status()
5. Handle exceptions gracefully and update error status in documents
6. Use appropriate indexes for your query patterns
7. Monitor storage usage regularly
8. Use the health check script for troubleshooting

""")


def print_configuration_options():
    """Print detailed configuration options."""
    print("""
MongoDB Configuration Options
=============================

Environment Variables (.env file):
----------------------------------

# Database Connection
MONGODB_HOST=localhost              # MongoDB server host
MONGODB_PORT=27017                  # MongoDB server port  
MONGODB_DATABASE=arxiv_scraper      # Database name
MONGODB_USERNAME=arxiv_app          # Application user
MONGODB_PASSWORD=secure_password    # Application password
MONGODB_ADMIN_PASSWORD=admin_pass   # Admin password

# Connection Pool Settings
MONGODB_MAX_POOL_SIZE=50           # Maximum connections per pool
MONGODB_MIN_POOL_SIZE=10           # Minimum connections per pool
MONGODB_TIMEOUT_MS=30000           # Connection timeout

# Storage Configuration
STORAGE_BASE_PATH=/mnt/data/arxiv_papers  # Base storage directory
MAX_STORAGE_GB=300                        # Maximum storage limit
PAPERS_SUBDIR=papers                      # Papers subdirectory
BOOKS_SUBDIR=books                        # Books subdirectory
ARTICLES_SUBDIR=articles                  # Articles subdirectory

# Performance Tuning
BATCH_SIZE=100                     # Default batch size for operations
MAX_WORKERS=4                      # Maximum worker threads
ENABLE_TEXT_EXTRACTION=true        # Enable text extraction
LOG_LEVEL=INFO                     # Logging level

# Agent-Specific Settings
ENABLE_CRAWLER_AGENT=true          # Enable crawler agent
ENABLE_SCRAPER_AGENT=true          # Enable scraper agent
ENABLE_DOWNLOADER_AGENT=true       # Enable downloader agent
ENABLE_NLP_AGENT=false             # Enable NLP agent

MongoDB Configuration (mongodb.conf):
------------------------------------

# Storage settings for /mnt/data
storage:
  dbPath: /mnt/data/mongodb/data
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4  # Adjust based on available RAM
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

# Network settings
net:
  port: 27017
  bindIp: 127.0.0.1
  maxIncomingConnections: 200

# Security
security:
  authorization: enabled

# Logging
systemLog:
  destination: file
  path: /mnt/data/mongodb/logs/mongod.log
  logAppend: true

Collection Schemas:
==================

Papers Collection (papers):
- paper_id (unique): arXiv ID, DOI, etc.
- source: "arxiv", "journal", "preprint"
- title: Paper title
- authors: Array of author names
- abstract: Paper abstract
- categories: Array of subject categories
- date_published: Publication date
- pdf_url: URL to PDF file
- pdf_downloaded: Boolean download status
- source_metadata: Source-specific fields
- processing_status: "pending", "processed", "error"

Books Collection (books):
- book_id (unique): Gutenberg ID, ISBN, etc.
- source: "gutenberg", "archive_org"
- title: Book title
- authors: Array of author names
- subjects: Array of book subjects
- language: Book language
- formats: Array of available formats
- pdf_url: URL to PDF file

Articles Collection (articles):
- article_id (unique): DOI, URL hash, etc.
- source: "journal", "magazine", "blog"
- title: Article title
- authors: Array of author names
- journal: Journal name
- doi: Digital Object Identifier
- date_published: Publication date

Index Strategy:
==============

High-performance indexes are automatically created for:
- Unique identifiers (paper_id, book_id, article_id)
- Source types and categories
- Publication dates (descending for recent-first queries)
- Download and processing status
- Full-text search on titles and abstracts
- Author name lookups

Storage Optimization:
====================

- Snappy compression for collections and indexes
- Prefix compression for indexes
- WiredTiger storage engine optimized for concurrent access
- Journal enabled for data durability
- Configurable cache size based on available RAM

Monitoring and Maintenance:
==========================

Use these scripts for ongoing maintenance:

# Check database health
python scripts/db_health_check.py

# Optimize performance
python scripts/optimize_mongodb.py --report

# View connection pool status
python -c "from arxiv_scraper.database.agent_pool_manager import get_agent_pool_manager; print(get_agent_pool_manager().get_pool_status())"

# Check storage usage
df -h /mnt/data

# View MongoDB logs
sudo tail -f /mnt/data/mongodb/logs/mongod.log

""")


def main():
    """Main function to display setup information."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MongoDB Setup Guide for arXiv Scraper")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")
    parser.add_argument("--examples", action="store_true", help="Show agent usage examples")
    parser.add_argument("--config", action="store_true", help="Show configuration options")
    parser.add_argument("--all", action="store_true", help="Show all information")
    
    args = parser.parse_args()
    
    if args.all or (not any([args.setup, args.examples, args.config])):
        print_setup_instructions()
        print_agent_usage_examples()
        print_configuration_options()
    else:
        if args.setup:
            print_setup_instructions()
        
        if args.examples:
            print_agent_usage_examples()
        
        if args.config:
            print_configuration_options()


if __name__ == "__main__":
    main()