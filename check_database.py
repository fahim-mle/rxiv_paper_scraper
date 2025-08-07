#!/usr/bin/env python3
"""
Quick script to check database contents
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from arxiv_scraper.database.mongodb_operations import get_operations

def main():
    db_ops = get_operations()
    
    # Get some papers from database
    papers = db_ops.find_papers({}, limit=3)
    
    print("Sample papers in database:")
    print("=" * 50)
    
    for paper in papers:
        print(f"Title: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'][:2])}...")
        print(f"arXiv ID: {paper['paper_id']}")
        print(f"PDF Downloaded: {'Yes' if paper['pdf_downloaded'] else 'No'}")
        print(f"Categories: {', '.join(paper['categories'])}")
        print("-" * 30)

    # Get collection stats
    stats = db_ops.get_collection_stats()
    print(f"\nDatabase Stats:")
    for collection, data in stats.items():
        print(f"  {collection}: {data['document_count']} papers, {data['downloaded_count']} with PDFs")

if __name__ == "__main__":
    main()