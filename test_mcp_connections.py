#!/usr/bin/env python3
"""
Test script to check MCP server connections and functionality.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from arxiv_scraper.mcp_servers.client_manager import MCPClientManager
from arxiv_scraper.utils.logger import get_logger


async def test_server_connections():
    """Test all MCP server connections."""
    logger = get_logger(__name__)
    manager = MCPClientManager()
    
    logger.info("Starting MCP server connection tests...")
    
    # Test individual server connections
    servers_to_test = ["arxiv", "playwright", "unstructured", "fetch", "tinybird", "piloty"]
    
    connection_results = {}
    
    for server_name in servers_to_test:
        logger.info(f"Testing connection to {server_name} MCP server...")
        
        try:
            success = await manager.connect_server(server_name)
            connection_results[server_name] = {
                "connected": success,
                "status": manager.get_server_status(server_name).value,
                "tools": manager.get_available_tools(server_name),
                "error": None
            }
            
            if success:
                logger.info(f"✓ {server_name} server connected successfully")
                
                # Test health check
                try:
                    health_ok = await manager.clients[server_name].health_check()
                    connection_results[server_name]["health_check"] = health_ok
                    if health_ok:
                        logger.info(f"✓ {server_name} health check passed")
                    else:
                        logger.warning(f"⚠ {server_name} health check failed")
                except Exception as e:
                    logger.warning(f"⚠ {server_name} health check error: {e}")
                    connection_results[server_name]["health_check"] = False
            else:
                logger.error(f"✗ {server_name} server connection failed")
                
        except Exception as e:
            logger.error(f"✗ {server_name} server error: {e}")
            connection_results[server_name] = {
                "connected": False,
                "status": "error",
                "tools": [],
                "error": str(e),
                "health_check": False
            }
    
    # Test batch connection
    logger.info("\nTesting batch connection...")
    batch_results = await manager.connect_all_servers()
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("MCP SERVER CONNECTION SUMMARY")
    logger.info("="*60)
    
    connected_count = 0
    total_count = len(servers_to_test)
    
    for server_name in servers_to_test:
        result = connection_results[server_name]
        status_icon = "✓" if result["connected"] else "✗"
        health_icon = "✓" if result.get("health_check") else "✗"
        
        logger.info(f"{status_icon} {server_name:12} | Status: {result['status']:12} | Health: {health_icon} | Tools: {len(result['tools'])}")
        
        if result["connected"]:
            connected_count += 1
        
        if result.get("error"):
            logger.info(f"  Error: {result['error']}")
    
    logger.info("="*60)
    logger.info(f"Connected: {connected_count}/{total_count} servers")
    
    if connected_count == 0:
        logger.warning("⚠ No MCP servers are currently running or accessible")
        logger.info("To start MCP servers, you need to:")
        logger.info("1. Clone the required repositories")
        logger.info("2. Install dependencies")  
        logger.info("3. Start each server on the configured ports")
        logger.info("See the configuration files in arxiv_scraper/mcp_servers/*/config.json")
    elif connected_count < total_count:
        logger.warning(f"⚠ Only {connected_count} out of {total_count} servers are available")
        logger.info("The system will work with reduced functionality")
    else:
        logger.info("✓ All MCP servers are connected and healthy!")
    
    # Test some basic tool calls if any servers are connected
    if connected_count > 0:
        logger.info("\n" + "="*60)
        logger.info("TESTING BASIC TOOL FUNCTIONALITY")
        logger.info("="*60)
        
        # Test arXiv server if connected
        if connection_results.get("arxiv", {}).get("connected"):
            try:
                logger.info("Testing arXiv search_papers tool...")
                response = await manager.call_tool(
                    "arxiv", 
                    "search_papers", 
                    {"query": "cat:cs.AI", "max_results": 2}
                )
                logger.info(f"✓ arXiv search returned {len(response.get('papers', []))} papers")
            except Exception as e:
                logger.error(f"✗ arXiv tool test failed: {e}")
        
        # Test fetch server if connected  
        if connection_results.get("fetch", {}).get("connected"):
            try:
                logger.info("Testing fetch server...")
                response = await manager.call_tool(
                    "fetch",
                    "fetch_url",
                    {"url": "https://httpbin.org/json", "timeout": 10}
                )
                logger.info("✓ Fetch tool test successful")
            except Exception as e:
                logger.error(f"✗ Fetch tool test failed: {e}")
    
    # Cleanup
    logger.info("\nDisconnecting from servers...")
    await manager.disconnect_all_servers()
    
    return connection_results


async def test_agent_integration():
    """Test the enhanced agents with MCP integration."""
    logger = get_logger(__name__)
    
    logger.info("\n" + "="*60)
    logger.info("TESTING ENHANCED AGENT INTEGRATION")
    logger.info("="*60)
    
    # Test Crawler Agent
    try:
        from arxiv_scraper.crawler.mcp_enhanced_crawler import MCPEnhancedCrawlerAgent
        
        crawler = MCPEnhancedCrawlerAgent()
        init_success = await crawler.initialize()
        
        if init_success:
            logger.info("✓ Enhanced Crawler Agent initialized successfully")
            
            # Test server status check
            status = await crawler.get_server_status()
            logger.info(f"Crawler server status: {status}")
            
        else:
            logger.warning("⚠ Enhanced Crawler Agent initialization failed")
            
        await crawler.shutdown()
        
    except Exception as e:
        logger.error(f"✗ Crawler Agent test failed: {e}")
    
    # Test Scraper Agent
    try:
        from arxiv_scraper.scraper.mcp_enhanced_scraper import MCPEnhancedScraperAgent
        
        scraper = MCPEnhancedScraperAgent()
        init_success = await scraper.initialize()
        
        if init_success:
            logger.info("✓ Enhanced Scraper Agent initialized successfully")
            
            # Test server status check
            status = await scraper.get_server_status()
            logger.info(f"Scraper server status: {status}")
        else:
            logger.warning("⚠ Enhanced Scraper Agent initialization failed")
            
        await scraper.shutdown()
        
    except Exception as e:
        logger.error(f"✗ Scraper Agent test failed: {e}")
    
    # Test Downloader Agent
    try:
        from arxiv_scraper.downloader_agent import MCPEnhancedDownloaderAgent
        
        downloader = MCPEnhancedDownloaderAgent()
        init_success = await downloader.initialize()
        
        if init_success:
            logger.info("✓ Enhanced Downloader Agent initialized successfully")
        else:
            logger.warning("⚠ Enhanced Downloader Agent initialization failed")
            
        await downloader.shutdown()
        
    except Exception as e:
        logger.error(f"✗ Downloader Agent test failed: {e}")


async def main():
    """Main test function."""
    logger = get_logger(__name__)
    
    logger.info("Starting arXiv Scraper MCP Integration Tests")
    logger.info("=" * 80)
    
    try:
        # Test server connections
        connection_results = await test_server_connections()
        
        # Test agent integration
        await test_agent_integration()
        
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)
        
        connected_servers = sum(1 for r in connection_results.values() if r["connected"])
        total_servers = len(connection_results)
        
        if connected_servers == 0:
            logger.info("Status: MCP servers not running - system will use fallback methods")
            logger.info("Action: Install and start MCP servers for full functionality")
        elif connected_servers < total_servers:
            logger.info(f"Status: Partial functionality ({connected_servers}/{total_servers} servers)")
            logger.info("Action: Start remaining servers for full functionality")
        else:
            logger.info("Status: Full MCP integration ready!")
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('mcp_test.log')
        ]
    )
    
    # Run tests
    asyncio.run(main())