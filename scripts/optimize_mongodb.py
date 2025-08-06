#!/usr/bin/env python3
"""
MongoDB Optimization Script for arXiv Scraper Project

Analyzes and optimizes MongoDB performance for high-throughput academic paper storage.
"""

import sys
import json
import psutil
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from arxiv_scraper.database.mongodb_connector import get_connector
from arxiv_scraper.config.settings import get_settings


class MongoDBOptimizer:
    """MongoDB performance optimization and tuning."""
    
    def __init__(self):
        self.connector = get_connector()
        self.settings = get_settings()
        
    def analyze_system_resources(self) -> Dict[str, Any]:
        """Analyze system resources for optimization recommendations."""
        # Get system memory
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/mnt/data')
        
        # Get CPU info
        cpu_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent(interval=1)
        
        return {
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": round((disk.used / disk.total) * 100, 2)
            },
            "cpu": {
                "cores": cpu_count,
                "usage_percent": cpu_usage
            }
        }
    
    def get_current_mongodb_config(self) -> Dict[str, Any]:
        """Get current MongoDB configuration parameters."""
        try:
            db = self.connector.connect()
            admin = self.connector._client.admin
            
            # Get current server parameters
            server_params = admin.command("getParameter", "*")
            server_status = admin.command("serverStatus")
            
            wired_tiger = server_status.get("wiredTiger", {})
            cache_stats = wired_tiger.get("cache", {})
            
            return {
                "cache_size_gb": cache_stats.get("maximum bytes configured", 0) / (1024**3),
                "current_cache_usage": cache_stats.get("bytes currently in the cache", 0) / (1024**3),
                "max_connections": server_params.get("maxIncomingConnections", 65536),
                "journal_enabled": server_params.get("storage.journal.enabled", True),
                "oplog_size_mb": server_status.get("repl", {}).get("logSizeMB", 0)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def recommend_cache_size(self, system_info: Dict[str, Any]) -> float:
        """Recommend optimal cache size based on available memory."""
        available_memory_gb = system_info["memory"]["available_gb"]
        
        # MongoDB WiredTiger recommends using 50% of available RAM for cache
        # Leave some room for OS and other processes
        if available_memory_gb >= 8:
            # For systems with plenty of RAM
            recommended_cache_gb = max(2, available_memory_gb * 0.4)
        elif available_memory_gb >= 4:
            # For moderate systems
            recommended_cache_gb = available_memory_gb * 0.35
        else:
            # For low-memory systems
            recommended_cache_gb = max(1, available_memory_gb * 0.25)
        
        return round(recommended_cache_gb, 2)
    
    def recommend_connection_pool_size(self, system_info: Dict[str, Any]) -> Dict[str, int]:
        """Recommend connection pool sizes based on system resources."""
        cpu_cores = system_info["cpu"]["cores"]
        
        # Base recommendations on CPU cores and expected load
        # For academic paper scraping, we expect burst loads during crawling
        
        max_pool_size = min(100, cpu_cores * 10)  # Allow for concurrent agents
        min_pool_size = max(5, cpu_cores * 2)     # Keep some connections warm
        
        return {
            "max_pool_size": max_pool_size,
            "min_pool_size": min_pool_size
        }
    
    def analyze_index_usage(self) -> Dict[str, Any]:
        """Analyze index usage and provide optimization recommendations."""
        try:
            index_stats = {}
            
            for collection_name in ["papers", "books", "articles"]:
                collection = self.connector.get_collection(collection_name)
                
                # Get index stats
                stats = collection.aggregate([{"$indexStats": {}}])
                collection_indexes = {}
                
                for index_stat in stats:
                    index_name = index_stat["name"]
                    usage_count = index_stat["accesses"]["ops"]
                    
                    collection_indexes[index_name] = {
                        "usage_count": usage_count,
                        "since": index_stat["accesses"]["since"]
                    }
                
                index_stats[collection_name] = collection_indexes
            
            return index_stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def recommend_indexes(self) -> Dict[str, List[Dict[str, Any]]]:
        """Recommend additional indexes based on expected query patterns."""
        recommendations = {
            "papers": [
                {
                    "index": {"date_published": -1, "categories": 1},
                    "reason": "Optimize queries for recent papers in specific categories"
                },
                {
                    "index": {"pdf_downloaded": 1, "processing_status": 1},
                    "reason": "Optimize batch processing queries"
                },
                {
                    "index": {"source": 1, "date_published": -1},
                    "reason": "Optimize source-specific chronological queries"
                }
            ],
            "books": [
                {
                    "index": {"language": 1, "subjects": 1},
                    "reason": "Optimize language and subject filtering"
                },
                {
                    "index": {"pdf_downloaded": 1, "formats": 1},
                    "reason": "Optimize format availability queries"
                }
            ],
            "articles": [
                {
                    "index": {"journal": 1, "date_published": -1},
                    "reason": "Optimize journal-specific queries"
                },
                {
                    "index": {"doi": 1},
                    "reason": "Optimize DOI lookups (sparse index)"
                }
            ]
        }
        
        return recommendations
    
    def generate_optimized_config(self) -> str:
        """Generate optimized MongoDB configuration."""
        system_info = self.analyze_system_resources()
        cache_size = self.recommend_cache_size(system_info)
        
        config = f"""# Optimized MongoDB Configuration for arXiv Scraper Project
# Generated based on system analysis: {system_info['cpu']['cores']} cores, {system_info['memory']['total_gb']} GB RAM

# Network settings
net:
  port: 27017
  bindIp: 127.0.0.1,::1
  maxIncomingConnections: 200  # Increased for multi-agent access

# Storage settings optimized for academic papers
storage:
  dbPath: /mnt/data/mongodb/data
  journal:
    enabled: true
    commitIntervalMs: 300  # Faster commits for high write loads
  wiredTiger:
    engineConfig:
      cacheSizeGB: {cache_size}  # Optimized for available RAM
      directoryForIndexes: true
      configString: "eviction=(threads_min=4,threads_max=8)"  # Tuned eviction
    collectionConfig:
      blockCompressor: snappy  # Good balance of speed and compression
    indexConfig:
      prefixCompression: true

# System logging
systemLog:
  destination: file
  path: /mnt/data/mongodb/logs/mongod.log
  logAppend: true
  logRotate: rename
  component:
    query:
      verbosity: 1  # Log slow queries for optimization

# Process management
processManagement:
  fork: true
  pidFilePath: /mnt/data/mongodb/mongod.pid

# Security settings
security:
  authorization: enabled

# Operation profiling for performance monitoring
operationProfiling:
  slowOpThresholdMs: 100  # Profile operations slower than 100ms
  mode: slowOp

# Set parameters for optimization
setParameter:
  failIndexKeyTooLong: false  # Allow longer keys for academic titles
  notablescan: false  # Allow table scans during development
  logLevel: 1  # Moderate logging
  syncdelay: 60  # Sync every 60 seconds (default)
  
# Connection and cursor timeouts
net:
  maxIncomingConnections: 200
  
# Memory and performance tuning
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: {cache_size}
      statisticsLogDelaySecs: 300  # Log statistics every 5 minutes
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true"""

        return config
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        system_info = self.analyze_system_resources()
        current_config = self.get_current_mongodb_config()
        index_usage = self.analyze_index_usage()
        cache_recommendation = self.recommend_cache_size(system_info)
        pool_recommendations = self.recommend_connection_pool_size(system_info)
        index_recommendations = self.recommend_indexes()
        
        # Generate recommendations
        recommendations = []
        
        # Cache size recommendation
        current_cache = current_config.get("cache_size_gb", 0)
        if abs(current_cache - cache_recommendation) > 0.5:
            recommendations.append({
                "type": "cache_size",
                "current": f"{current_cache:.1f} GB",
                "recommended": f"{cache_recommendation:.1f} GB",
                "reason": "Optimize memory usage based on available RAM"
            })
        
        # Connection pool recommendations
        recommendations.append({
            "type": "connection_pool",
            "recommended": pool_recommendations,
            "reason": "Optimize for multi-agent concurrent access"
        })
        
        # Storage recommendations
        disk_usage = system_info["disk"]["usage_percent"]
        if disk_usage > 80:
            recommendations.append({
                "type": "storage",
                "current": f"{disk_usage:.1f}% used",
                "recommended": "Consider cleanup or expansion",
                "reason": "High disk usage may impact performance"
            })
        
        return {
            "system_info": system_info,
            "current_config": current_config,
            "index_usage": index_usage,
            "recommendations": recommendations,
            "index_recommendations": index_recommendations,
            "optimized_config_preview": self.generate_optimized_config()[:500] + "..."
        }


def main():
    """Main optimization function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MongoDB Optimization for arXiv Scraper")
    parser.add_argument("--report", action="store_true", help="Generate optimization report")
    parser.add_argument("--config", action="store_true", help="Generate optimized config file")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--apply", action="store_true", help="Apply optimization recommendations")
    
    args = parser.parse_args()
    
    optimizer = MongoDBOptimizer()
    
    if args.report:
        report = optimizer.generate_optimization_report()
        
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("MongoDB Optimization Report")
            print("=" * 50)
            
            # System info
            system = report["system_info"]
            print(f"System: {system['cpu']['cores']} cores, {system['memory']['total_gb']:.1f} GB RAM")
            print(f"Disk Usage: {system['disk']['usage_percent']:.1f}% ({system['disk']['free_gb']:.1f} GB free)")
            print()
            
            # Current config
            current = report["current_config"]
            if "error" not in current:
                print(f"Current Cache: {current.get('cache_size_gb', 0):.1f} GB")
                print(f"Max Connections: {current.get('max_connections', 'N/A')}")
                print()
            
            # Recommendations
            print("Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"{i}. {rec['type'].replace('_', ' ').title()}")
                print(f"   Current: {rec.get('current', 'N/A')}")
                print(f"   Recommended: {rec['recommended']}")
                print(f"   Reason: {rec['reason']}")
                print()
    
    elif args.config:
        config = optimizer.generate_optimized_config()
        
        if args.apply:
            # Write to mongodb.conf
            config_path = Path("mongodb.conf")
            config_path.write_text(config)
            print(f"Optimized configuration written to {config_path}")
            print("To apply: sudo cp mongodb.conf /etc/mongod.conf && sudo systemctl restart mongod")
        else:
            print(config)
    
    else:
        # Quick system analysis
        system_info = optimizer.analyze_system_resources()
        cache_rec = optimizer.recommend_cache_size(system_info)
        pool_rec = optimizer.recommend_connection_pool_size(system_info)
        
        print("Quick MongoDB Optimization Analysis")
        print("=" * 40)
        print(f"System: {system_info['cpu']['cores']} cores, {system_info['memory']['total_gb']:.1f} GB RAM")
        print(f"Recommended Cache Size: {cache_rec:.1f} GB")
        print(f"Recommended Connection Pool: {pool_rec['min_pool_size']}-{pool_rec['max_pool_size']}")
        print()
        print("Run with --report for detailed analysis")
        print("Run with --config to generate optimized configuration")


if __name__ == "__main__":
    main()