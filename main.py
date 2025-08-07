#!/usr/bin/env python3
"""
arXiv Paper Scraper - Main Entry Point

A comprehensive academic paper scraper focusing on AI/ML papers from arXiv.
Features multi-agent architecture for crawling, processing, and storing papers.
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from arxiv_scraper.crawler.arxiv_api import ArxivCrawler
from arxiv_scraper.scraper.metadata_parser import PaperMetadataProcessor
from arxiv_scraper.scraper.pdf_downloader import StorageManager, PDFDownloader
from arxiv_scraper.database.mongodb_operations import get_operations
from arxiv_scraper.utils.logger import get_logger


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


async def run_scraper(args):
    """Run the main scraper pipeline."""
    logger = get_logger("main")
    logger.info("Starting arXiv Paper Scraper")
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        
        db_ops = get_operations()
        if not db_ops.initialize_database():
            logger.error("Failed to initialize database")
            return False
        
        crawler = ArxivCrawler(rate_limit_delay=args.rate_limit)
        processor = PaperMetadataProcessor()
        storage = StorageManager(base_path=args.storage_path, max_storage_gb=args.max_storage)
        
        # Check storage space
        storage_stats = storage.get_storage_stats()
        logger.info(f"Storage: {storage_stats['current_usage_gb']:.1f}GB used, "
                   f"{storage_stats['available_gb']:.1f}GB available")
        
        if storage_stats['usage_percentage'] > 90:
            logger.warning("Storage is over 90% full!")
        
        # Crawl papers
        logger.info(f"Crawling up to {args.max_papers} papers...")
        
        if args.categories:
            categories = args.categories.split(',')
            papers = await crawler.crawl_specific_categories(
                categories=categories,
                max_papers=args.max_papers,
                days_back=args.days_back
            )
        else:
            # Default: AI/ML papers
            papers = await crawler.crawl_ai_ml_papers(
                max_papers=args.max_papers,
                days_back=args.days_back,
                additional_keywords=args.keywords.split(',') if args.keywords else None
            )
        
        if not papers:
            logger.error("No papers crawled")
            return False
        
        logger.info(f"Crawled {len(papers)} papers")
        
        # Process metadata
        logger.info("Processing metadata...")
        processed_papers = processor.process_paper_batch(papers)
        
        if not processed_papers:
            logger.error("No papers processed successfully")
            return False
        
        logger.info(f"Processed {len(processed_papers)} papers")
        
        # Store in database
        logger.info("Storing in database...")
        result = db_ops.bulk_insert_papers(processed_papers)
        logger.info(f"Stored {result['inserted']} papers, {result['errors']} errors")
        
        # Download PDFs if requested
        if args.download_pdfs:
            logger.info("Downloading PDFs...")
            
            async with PDFDownloader(storage, rate_limit_delay=args.pdf_rate_limit) as downloader:
                updated_papers = await downloader.download_papers_batch(
                    processed_papers,
                    max_concurrent=args.max_concurrent
                )
                
                stats = downloader.get_download_stats()
                logger.info(f"Downloaded {stats['successful']}/{stats['attempted']} PDFs "
                           f"({stats['total_size_mb']:.1f}MB)")
                
                # Update database with download status
                updated_count = 0
                for paper in updated_papers:
                    if paper.get("pdf_downloaded", False):
                        if db_ops.update_paper_download_status(
                            paper["paper_id"],
                            paper["pdf_file_path"],
                            paper["pdf_file_size"]
                        ):
                            updated_count += 1
                
                logger.info(f"Updated download status for {updated_count} papers")
        
        # Print summary
        collection_stats = db_ops.get_collection_stats()
        print("\n" + "=" * 50)
        print("SCRAPER RUN SUMMARY")
        print("=" * 50)
        print(f"Papers crawled:    {len(papers)}")
        print(f"Papers processed:  {len(processed_papers)}")
        print(f"Papers stored:     {result['inserted']}")
        
        if args.download_pdfs:
            print(f"PDFs downloaded:   {stats['successful']}")
            print(f"Download size:     {stats['total_size_mb']:.1f}MB")
        
        print(f"\nDatabase totals:")
        for collection, stats in collection_stats.items():
            print(f"  {collection}: {stats['document_count']} papers")
        
        logger.info("Scraper run completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Scraper run failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="arXiv AI/ML Paper Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --max-papers 50 --download-pdfs
  python main.py --categories "cs.AI,cs.LG" --days-back 14
  python main.py --keywords "transformer,attention" --max-papers 30
        """
    )
    
    # Basic options
    parser.add_argument("--max-papers", type=int, default=100,
                       help="Maximum number of papers to crawl (default: 100)")
    parser.add_argument("--days-back", type=int, default=30,
                       help="How many days back to search (default: 30)")
    parser.add_argument("--download-pdfs", action="store_true",
                       help="Download PDF files")
    
    # Filtering options
    parser.add_argument("--categories", type=str,
                       help="Comma-separated arXiv categories (e.g., cs.AI,cs.LG)")
    parser.add_argument("--keywords", type=str,
                       help="Comma-separated keywords to search for")
    
    # Storage options
    parser.add_argument("--storage-path", type=str, default="papers",
                       help="Base path for storing PDFs (default: papers)")
    parser.add_argument("--max-storage", type=int, default=300,
                       help="Maximum storage in GB (default: 300)")
    
    # Rate limiting options
    parser.add_argument("--rate-limit", type=float, default=3.0,
                       help="Delay between arXiv API requests in seconds (default: 3.0)")
    parser.add_argument("--pdf-rate-limit", type=float, default=2.0,
                       help="Delay between PDF downloads in seconds (default: 2.0)")
    parser.add_argument("--max-concurrent", type=int, default=2,
                       help="Maximum concurrent PDF downloads (default: 2)")
    
    # Logging options
    parser.add_argument("--log-level", type=str, default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level (default: INFO)")
    parser.add_argument("--log-file", type=str,
                       help="Log to file (default: console only)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Run scraper
    success = asyncio.run(run_scraper(args))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()