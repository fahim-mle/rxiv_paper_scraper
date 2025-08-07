#!/usr/bin/env python3
"""
AI/ML Paper Crawler for arXiv
Crawls 20 recent AI/ML papers from arXiv using the crawler agent.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

from arxiv_scraper.crawler.arxiv_api import ArxivCrawler
from arxiv_scraper.database.mongodb_operations import MongoDBOperations
from arxiv_scraper.utils.logger import get_logger

logger = get_logger(__name__)


class AIMLPaperCrawler:
    """Crawler for AI/ML papers from arXiv focused on recent research."""
    
    # Target AI/ML categories for focused crawling
    TARGET_CATEGORIES = [
        "cs.AI",    # Artificial Intelligence
        "cs.LG",    # Machine Learning
        "cs.CV",    # Computer Vision
        "cs.CL",    # Computation and Language (NLP)
        "cs.NE",    # Neural and Evolutionary Computing
        "stat.ML",  # Machine Learning (Statistics)
    ]
    
    def __init__(self):
        self.crawler = ArxivCrawler(rate_limit_delay=3.0)  # arXiv requires 3s delay
        self.db_ops = None
        
    async def initialize_database(self) -> bool:
        """Initialize database connection."""
        try:
            self.db_ops = MongoDBOperations()
            success = self.db_ops.initialize_database()
            if success:
                logger.info("Database connection established")
                return True
            else:
                logger.error("Failed to initialize database")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    async def crawl_recent_ai_ml_papers(self, max_papers: int = 20) -> List[Dict[str, Any]]:
        """
        Crawl recent AI/ML papers from arXiv.
        
        Args:
            max_papers: Maximum number of papers to crawl
            
        Returns:
            List of paper metadata dictionaries
        """
        logger.info(f"Starting crawl for {max_papers} recent AI/ML papers from arXiv")
        
        try:
            # Crawl papers using the ArxivCrawler
            papers = await self.crawler.crawl_specific_categories(
                categories=self.TARGET_CATEGORIES,
                max_papers=max_papers,
                days_back=7  # Focus on very recent papers (last week)
            )
            
            if not papers:
                logger.warning("No papers retrieved from arXiv")
                return []
            
            # Filter and enrich paper data
            filtered_papers = []
            for paper in papers:
                # Basic quality filters
                if (paper.get('title') and 
                    paper.get('abstract') and 
                    len(paper.get('authors', [])) > 0):
                    
                    # Add crawl metadata
                    paper['crawl_timestamp'] = datetime.now(timezone.utc)
                    paper['crawler_version'] = '1.0'
                    paper['crawl_source'] = 'arxiv_direct_api'
                    
                    filtered_papers.append(paper)
            
            logger.info(f"Successfully crawled {len(filtered_papers)} AI/ML papers")
            return filtered_papers
            
        except Exception as e:
            logger.error(f"Error during paper crawling: {e}")
            return []
    
    async def store_papers_to_database(self, papers: List[Dict[str, Any]]) -> bool:
        """
        Store crawled papers to MongoDB database.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        if not papers:
            logger.warning("No papers to store in database")
            return True
        
        if not self.db_ops:
            logger.error("Database not initialized")
            return False
        
        try:
            stored_count = 0
            duplicate_count = 0
            
            for paper in papers:
                # Check if paper already exists
                existing_papers = self.db_ops.find_papers({"paper_id": paper.get('paper_id')})
                
                if existing_papers:
                    duplicate_count += 1
                    logger.debug(f"Paper {paper.get('paper_id')} already exists, skipping")
                    continue
                
                # Store new paper
                result = self.db_ops.insert_paper(paper)
                if result:
                    stored_count += 1
                    logger.debug(f"Stored paper: {paper.get('title', 'Unknown')}")
                else:
                    logger.warning(f"Failed to store paper: {paper.get('paper_id')}")
            
            logger.info(f"Database storage complete: {stored_count} new papers, {duplicate_count} duplicates")
            return True
            
        except Exception as e:
            logger.error(f"Error storing papers to database: {e}")
            return False
    
    async def generate_crawl_report(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary report of the crawl."""
        if not papers:
            return {"status": "no_papers", "count": 0}
        
        # Analyze categories
        categories = {}
        authors_count = 0
        avg_abstract_length = 0
        
        for paper in papers:
            # Count categories
            for cat in paper.get('categories', []):
                categories[cat] = categories.get(cat, 0) + 1
            
            # Count authors
            authors_count += len(paper.get('authors', []))
            
            # Calculate average abstract length
            abstract = paper.get('abstract', '')
            avg_abstract_length += len(abstract)
        
        if papers:
            avg_authors = authors_count / len(papers)
            avg_abstract_length = avg_abstract_length / len(papers)
        else:
            avg_authors = 0
            avg_abstract_length = 0
        
        report = {
            "status": "success",
            "total_papers": len(papers),
            "categories_distribution": categories,
            "average_authors_per_paper": round(avg_authors, 2),
            "average_abstract_length": round(avg_abstract_length),
            "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
            "target_categories": self.TARGET_CATEGORIES,
            "sample_papers": [
                {
                    "title": p.get('title', 'Unknown'),
                    "authors": p.get('authors', [])[:3],  # First 3 authors
                    "categories": p.get('categories', []),
                    "paper_id": p.get('paper_id')
                }
                for p in papers[:5]  # First 5 papers as samples
            ]
        }
        
        return report
    
    async def run_complete_crawl(self, max_papers: int = 20) -> Dict[str, Any]:
        """
        Run complete crawl process: fetch papers, store to database, generate report.
        
        Args:
            max_papers: Maximum number of papers to crawl
            
        Returns:
            Crawl report dictionary
        """
        logger.info("Starting complete AI/ML paper crawl process")
        
        # Step 1: Initialize database
        db_initialized = await self.initialize_database()
        
        # Step 2: Crawl papers
        papers = await self.crawl_recent_ai_ml_papers(max_papers)
        
        # Step 3: Store to database (if available)
        storage_success = False
        if db_initialized and papers:
            storage_success = await self.store_papers_to_database(papers)
        
        # Step 4: Generate report
        report = await self.generate_crawl_report(papers)
        report['database_storage'] = storage_success
        report['database_initialized'] = db_initialized
        
        # No cleanup needed for this database implementation
        
        return report


async def main():
    """Main function to run the AI/ML paper crawler."""
    crawler = AIMLPaperCrawler()
    
    try:
        # Run the complete crawl process
        report = await crawler.run_complete_crawl(max_papers=20)
        
        # Display results
        print("\n" + "="*80)
        print("AI/ML PAPER CRAWL RESULTS")
        print("="*80)
        print(f"Status: {report.get('status', 'unknown')}")
        print(f"Total papers crawled: {report.get('total_papers', 0)}")
        print(f"Database initialized: {report.get('database_initialized', False)}")
        print(f"Database storage successful: {report.get('database_storage', False)}")
        print(f"Average authors per paper: {report.get('average_authors_per_paper', 0)}")
        print(f"Average abstract length: {report.get('average_abstract_length', 0)} characters")
        
        print("\nCategory Distribution:")
        categories = report.get('categories_distribution', {})
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count} papers")
        
        print("\nSample Papers:")
        for i, paper in enumerate(report.get('sample_papers', [])[:3], 1):
            print(f"\n  {i}. {paper.get('title', 'Unknown')}")
            print(f"     Authors: {', '.join(paper.get('authors', [])[:2])}")
            print(f"     Categories: {', '.join(paper.get('categories', []))}")
            print(f"     ID: {paper.get('paper_id', 'Unknown')}")
        
        # Save detailed report to file
        report_filename = f"crawl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_filename}")
        print("="*80)
        
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user")
    except Exception as e:
        logger.error(f"Crawl failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())