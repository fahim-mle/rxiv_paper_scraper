#!/usr/bin/env python3
"""
Test Script for arXiv AI/ML Paper Scraper

This script tests the complete pipeline:
1. Crawl 20 AI/ML papers from arXiv
2. Parse and validate metadata
3. Store in MongoDB
4. Download PDFs

Run this script to test the complete system.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from arxiv_scraper.crawler.arxiv_api import ArxivCrawler
from arxiv_scraper.scraper.metadata_parser import PaperMetadataProcessor
from arxiv_scraper.scraper.pdf_downloader import StorageManager, PDFDownloader
from arxiv_scraper.database.mongodb_operations import get_operations
from arxiv_scraper.utils.logger import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper_test.log')
    ]
)

logger = get_logger(__name__)


async def test_complete_pipeline():
    """Test the complete scraping pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Complete arXiv AI/ML Paper Scraper Test")
    logger.info("=" * 60)
    
    try:
        # Step 1: Initialize components
        logger.info("Step 1: Initializing components...")
        
        # Initialize database operations
        db_ops = get_operations()
        if not db_ops.initialize_database():
            logger.error("Failed to initialize database")
            return False
        
        # Initialize crawler, processor, and storage
        crawler = ArxivCrawler(rate_limit_delay=3.0)
        processor = PaperMetadataProcessor()
        storage = StorageManager(base_path="papers", max_storage_gb=300)
        
        logger.info("✓ Components initialized successfully")
        
        # Step 2: Crawl papers from arXiv
        logger.info("Step 2: Crawling 20 AI/ML papers from arXiv...")
        
        papers = await crawler.crawl_ai_ml_papers(
            max_papers=20,
            days_back=90,  # Last 90 days for more content
            additional_keywords=["transformer", "llm", "gpt", "bert"]
        )
        
        if not papers:
            logger.error("No papers crawled from arXiv")
            return False
        
        logger.info(f"✓ Successfully crawled {len(papers)} papers")
        
        # Step 3: Process and validate metadata
        logger.info("Step 3: Processing and validating metadata...")
        
        processed_papers = processor.process_paper_batch(papers)
        
        if not processed_papers:
            logger.error("No papers processed successfully")
            return False
        
        logger.info(f"✓ Successfully processed {len(processed_papers)} papers")
        
        # Step 4: Store metadata in MongoDB
        logger.info("Step 4: Storing metadata in MongoDB...")
        
        insertion_result = db_ops.bulk_insert_papers(processed_papers)
        
        logger.info(f"✓ Stored {insertion_result['inserted']} papers in database")
        if insertion_result['errors'] > 0:
            logger.warning(f"  {insertion_result['errors']} papers had insertion errors")
        
        # Step 5: Download PDFs
        logger.info("Step 5: Downloading PDF files...")
        
        # Check storage space
        storage_stats = storage.get_storage_stats()
        logger.info(f"Storage status: {storage_stats['current_usage_gb']:.2f}GB used, "
                   f"{storage_stats['available_gb']:.2f}GB available")
        
        async with PDFDownloader(storage, rate_limit_delay=2.0) as downloader:
            updated_papers = await downloader.download_papers_batch(
                processed_papers,
                max_concurrent=2  # Conservative to respect rate limits
            )
            
            download_stats = downloader.get_download_stats()
            logger.info(f"✓ Download completed: {download_stats}")
        
        # Step 6: Update database with download information
        logger.info("Step 6: Updating database with download status...")
        
        updated_count = 0
        for paper in updated_papers:
            if paper.get("pdf_downloaded", False):
                success = db_ops.update_paper_download_status(
                    paper["paper_id"],
                    paper["pdf_file_path"],
                    paper["pdf_file_size"]
                )
                if success:
                    updated_count += 1
        
        logger.info(f"✓ Updated download status for {updated_count} papers")
        
        # Step 7: Generate final report
        logger.info("Step 7: Generating final report...")
        
        # Get collection statistics
        collection_stats = db_ops.get_collection_stats()
        
        # Print detailed report
        print("\n" + "=" * 60)
        print("SCRAPING TEST RESULTS")
        print("=" * 60)
        print(f"Papers crawled:     {len(papers)}")
        print(f"Papers processed:   {len(processed_papers)}")
        print(f"Papers stored:      {insertion_result['inserted']}")
        print(f"PDFs downloaded:    {download_stats['successful']}")
        print(f"Download success:   {download_stats['success_rate']:.1f}%")
        print(f"Total data size:    {download_stats['total_size_mb']:.2f} MB")
        print("\nDatabase Statistics:")
        for collection, stats in collection_stats.items():
            print(f"  {collection}: {stats['document_count']} docs, "
                  f"{stats['downloaded_count']} with PDFs")
        
        print(f"\nStorage Statistics:")
        storage_stats = storage.get_storage_stats()
        print(f"  Current usage: {storage_stats['current_usage_gb']:.2f}GB "
              f"({storage_stats['usage_percentage']:.1f}%)")
        print(f"  Available space: {storage_stats['available_gb']:.2f}GB")
        
        # Sample some papers for verification
        print("\nSample Papers:")
        print("-" * 40)
        for i, paper in enumerate(processed_papers[:3]):
            print(f"{i+1}. {paper['title'][:80]}...")
            print(f"   Authors: {', '.join(paper['authors'][:2])}")
            print(f"   arXiv ID: {paper['paper_id']}")
            print(f"   Categories: {', '.join(paper['categories'][:3])}")
            print(f"   PDF Downloaded: {'Yes' if paper.get('pdf_downloaded') else 'No'}")
            print()
        
        logger.info("✓ Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False


async def quick_test_crawler():
    """Quick test of just the crawler component."""
    logger.info("Running quick crawler test...")
    
    crawler = ArxivCrawler()
    papers = await crawler.crawl_ai_ml_papers(max_papers=5, days_back=3)
    
    print(f"\nCrawled {len(papers)} papers:")
    for paper in papers:
        print(f"- {paper['title'][:60]}... (ID: {paper['paper_id']})")
    
    return papers


def test_database_connection():
    """Test database connection and setup."""
    logger.info("Testing database connection...")
    
    try:
        db_ops = get_operations()
        if db_ops.initialize_database():
            stats = db_ops.get_collection_stats()
            print(f"Database connected successfully. Collections: {list(stats.keys())}")
            return True
        else:
            print("Database initialization failed")
            return False
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test arXiv AI/ML Paper Scraper")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick crawler test only")
    parser.add_argument("--db-test", action="store_true",
                       help="Test database connection only")
    
    args = parser.parse_args()
    
    if args.db_test:
        success = test_database_connection()
        sys.exit(0 if success else 1)
    elif args.quick:
        asyncio.run(quick_test_crawler())
    else:
        success = asyncio.run(test_complete_pipeline())
        sys.exit(0 if success else 1)