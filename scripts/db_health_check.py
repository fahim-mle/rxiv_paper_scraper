#!/usr/bin/env python3
"""
MongoDB Health Check Script for arXiv Scraper Project

Monitors database health, performance, and storage usage for the multi-agent system.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from arxiv_scraper.database.mongodb_connector import get_connector
from arxiv_scraper.database.mongodb_operations import get_operations
from arxiv_scraper.config.settings import get_settings


class DatabaseHealthChecker:
    """MongoDB health monitoring and diagnostics."""
    
    def __init__(self):
        self.connector = get_connector()
        self.operations = get_operations()
        self.settings = get_settings()
        
    def check_connection(self) -> Dict[str, Any]:
        """Check basic connectivity."""
        start_time = time.time()
        
        try:
            success = self.connector.test_connection()
            response_time = (time.time() - start_time) * 1000  # ms
            
            if success:
                server_info = self.connector.get_server_info()
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "mongodb_version": server_info.get("version"),
                    "uptime_seconds": server_info.get("uptime")
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time_ms": round(response_time, 2),
                    "error": "Connection test failed"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }
    
    def check_collections(self) -> Dict[str, Any]:
        """Check collection health and document counts."""
        try:
            collections = self.connector.list_collections()
            stats = self.operations.get_collection_stats()
            
            collection_health = {}
            total_documents = 0
            
            for collection in ["papers", "books", "articles", "metadata"]:
                if collection in collections:
                    collection_stats = stats.get(collection, {})
                    doc_count = collection_stats.get("document_count", 0)
                    total_documents += doc_count
                    
                    collection_health[collection] = {
                        "exists": True,
                        "document_count": doc_count,
                        "downloaded_count": collection_stats.get("downloaded_count", 0),
                        "pending_count": collection_stats.get("pending_count", 0)
                    }
                else:
                    collection_health[collection] = {
                        "exists": False,
                        "error": "Collection not found"
                    }
            
            return {
                "status": "healthy" if total_documents >= 0 else "warning",
                "total_documents": total_documents,
                "collections": collection_health
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_indexes(self) -> Dict[str, Any]:
        """Check index health and performance."""
        try:
            index_info = {}
            
            for collection_name in ["papers", "books", "articles"]:
                collection = self.connector.get_collection(collection_name)
                indexes = collection.list_indexes()
                
                index_list = []
                for index in indexes:
                    index_list.append({
                        "name": index.get("name"),
                        "key": index.get("key"),
                        "unique": index.get("unique", False)
                    })
                
                index_info[collection_name] = {
                    "count": len(index_list),
                    "indexes": index_list
                }
            
            return {
                "status": "healthy",
                "collections": index_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_storage_usage(self) -> Dict[str, Any]:
        """Check storage usage and capacity."""
        try:
            db_stats = self.connector.get_database_stats()
            
            # Database size info
            data_size_mb = db_stats.get("dataSize", 0) / (1024 * 1024)
            storage_size_mb = db_stats.get("storageSize", 0) / (1024 * 1024)
            index_size_mb = db_stats.get("indexSize", 0) / (1024 * 1024)
            total_size_mb = data_size_mb + index_size_mb
            
            # Calculate storage percentage
            max_storage_gb = self.settings.storage.max_storage_gb
            max_storage_mb = max_storage_gb * 1024
            usage_percentage = (total_size_mb / max_storage_mb) * 100
            
            # Determine status based on usage
            if usage_percentage < 70:
                status = "healthy"
            elif usage_percentage < 85:
                status = "warning"
            else:
                status = "critical"
            
            return {
                "status": status,
                "data_size_mb": round(data_size_mb, 2),
                "storage_size_mb": round(storage_size_mb, 2),
                "index_size_mb": round(index_size_mb, 2),
                "total_size_mb": round(total_size_mb, 2),
                "max_storage_gb": max_storage_gb,
                "usage_percentage": round(usage_percentage, 2),
                "available_mb": round(max_storage_mb - total_size_mb, 2)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_performance(self) -> Dict[str, Any]:
        """Check database performance metrics."""
        try:
            # Simple performance test - measure time for basic operations
            start_time = time.time()
            
            # Test query performance
            collection = self.connector.get_collection("papers")
            collection.count_documents({})  # Simple count query
            
            query_time = (time.time() - start_time) * 1000
            
            # Get server status for more metrics
            server_status = self.connector._client.admin.command("serverStatus")
            
            connections = server_status.get("connections", {})
            operations = server_status.get("opcounters", {})
            
            return {
                "status": "healthy" if query_time < 1000 else "warning",
                "query_response_time_ms": round(query_time, 2),
                "connections": {
                    "current": connections.get("current", 0),
                    "available": connections.get("available", 0)
                },
                "operations": {
                    "insert": operations.get("insert", 0),
                    "query": operations.get("query", 0),
                    "update": operations.get("update", 0),
                    "delete": operations.get("delete", 0)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def run_full_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        health_report = {
            "timestamp": time.time(),
            "database_name": self.settings.database.database_name,
            "checks": {
                "connection": self.check_connection(),
                "collections": self.check_collections(),
                "indexes": self.check_indexes(),
                "storage": self.check_storage_usage(),
                "performance": self.check_performance()
            }
        }
        
        # Determine overall health status
        statuses = [check.get("status") for check in health_report["checks"].values()]
        
        if "error" in statuses:
            overall_status = "error"
        elif "critical" in statuses:
            overall_status = "critical"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        health_report["overall_status"] = overall_status
        
        return health_report


def main():
    """Main health check function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MongoDB Health Check for arXiv Scraper")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--check", choices=["connection", "collections", "indexes", "storage", "performance"],
                       help="Run specific check only")
    
    args = parser.parse_args()
    
    checker = DatabaseHealthChecker()
    
    if args.check:
        # Run specific check
        check_method = getattr(checker, f"check_{args.check}")
        result = check_method()
    else:
        # Run full health check
        result = checker.run_full_health_check()
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Pretty print results
        if args.check:
            print(f"MongoDB {args.check.title()} Check:")
            print(f"Status: {result.get('status', 'unknown')}")
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                for key, value in result.items():
                    if key not in ["status", "error"]:
                        print(f"{key}: {value}")
        else:
            print("MongoDB Health Check Report")
            print("=" * 40)
            print(f"Overall Status: {result['overall_status'].upper()}")
            print(f"Database: {result['database_name']}")
            print()
            
            for check_name, check_result in result["checks"].items():
                status = check_result.get("status", "unknown")
                print(f"{check_name.title()}: {status.upper()}")
                
                if check_result.get("error"):
                    print(f"  Error: {check_result['error']}")
                elif check_name == "storage":
                    print(f"  Usage: {check_result.get('usage_percentage', 0):.1f}%")
                    print(f"  Total Size: {check_result.get('total_size_mb', 0):.2f} MB")
                elif check_name == "collections":
                    print(f"  Total Documents: {check_result.get('total_documents', 0)}")
                elif check_name == "connection":
                    print(f"  Response Time: {check_result.get('response_time_ms', 0):.2f} ms")
            
            print()
    
    # Exit with appropriate code
    if isinstance(result, dict) and result.get("overall_status") in ["error", "critical"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()