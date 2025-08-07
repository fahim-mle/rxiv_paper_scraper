#!/usr/bin/env python3
"""
Docker-compatible MCP Server startup script for arXiv Scraper.
This script runs MCP servers in a container-friendly way.
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Dict, List
import subprocess
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/mcp_servers/docker_startup.log')
    ]
)

logger = logging.getLogger(__name__)

class MCPServerManager:
    """Manages MCP servers in Docker environment."""
    
    def __init__(self):
        self.servers: Dict[str, subprocess.Popen] = {}
        self.shutdown_event = asyncio.Event()
        
        # Server configurations
        self.server_configs = [
            {
                'name': 'arxiv',
                'command': ['python', '-m', 'arxiv_mcp_server', '--storage-path', '/app/papers/'],
                'port': 3001,
                'essential': True
            },
            {
                'name': 'fetch',
                'command': ['mcp-server-fetch'],
                'port': 3004,
                'essential': True
            }
        ]
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def start_server(self, config: dict) -> bool:
        """Start a single MCP server."""
        name = config['name']
        command = config['command']
        
        try:
            logger.info(f"Starting {name} MCP server...")
            
            # Setup logs
            log_file = open(f'/app/logs/mcp_servers/{name}.log', 'w')
            
            # Start server process
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            
            self.servers[name] = process
            
            # Give server time to start
            await asyncio.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info(f"✓ {name} server started successfully (PID: {process.pid})")
                return True
            else:
                logger.error(f"✗ {name} server failed to start (exit code: {process.poll()})")
                return False
                
        except Exception as e:
            logger.error(f"Error starting {name} server: {e}")
            return False
    
    async def stop_server(self, name: str):
        """Stop a single MCP server."""
        if name not in self.servers:
            return
        
        process = self.servers[name]
        
        try:
            logger.info(f"Stopping {name} server (PID: {process.pid})...")
            
            # Try graceful shutdown first
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Wait for graceful shutdown
            for _ in range(10):
                if process.poll() is not None:
                    break
                await asyncio.sleep(1)
            
            # Force kill if still running
            if process.poll() is None:
                logger.warning(f"Force killing {name} server...")
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                await asyncio.sleep(1)
            
            logger.info(f"✓ {name} server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping {name} server: {e}")
        
        finally:
            del self.servers[name]
    
    async def start_all_servers(self) -> bool:
        """Start all configured MCP servers."""
        logger.info("Starting all MCP servers...")
        
        success_count = 0
        essential_count = 0
        
        for config in self.server_configs:
            success = await self.start_server(config)
            if success:
                success_count += 1
            
            if config.get('essential', False):
                essential_count += 1
                if not success:
                    logger.error(f"Essential server {config['name']} failed to start")
                    return False
        
        logger.info(f"Started {success_count}/{len(self.server_configs)} MCP servers")
        
        # At least one essential server must be running
        return essential_count > 0 and success_count >= essential_count
    
    async def stop_all_servers(self):
        """Stop all running MCP servers."""
        logger.info("Stopping all MCP servers...")
        
        # Stop servers in reverse order
        server_names = list(self.servers.keys())
        for name in reversed(server_names):
            await self.stop_server(name)
        
        logger.info("All MCP servers stopped")
    
    async def monitor_servers(self):
        """Monitor server health and restart failed essential servers."""
        while not self.shutdown_event.is_set():
            try:
                # Check each server
                failed_servers = []
                
                for config in self.server_configs:
                    name = config['name']
                    
                    if name in self.servers:
                        process = self.servers[name]
                        if process.poll() is not None:
                            logger.warning(f"{name} server died (exit code: {process.poll()})")
                            failed_servers.append(config)
                            del self.servers[name]
                
                # Restart failed essential servers
                for config in failed_servers:
                    if config.get('essential', False):
                        logger.info(f"Restarting essential server {config['name']}...")
                        await self.start_server(config)
                
                # Sleep before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in server monitoring: {e}")
                await asyncio.sleep(10)
    
    async def run(self):
        """Main run loop."""
        self.setup_signal_handlers()
        
        # Start all servers
        if not await self.start_all_servers():
            logger.error("Failed to start essential MCP servers")
            return 1
        
        logger.info("MCP Server Manager started successfully")
        logger.info("Available servers:")
        for name, process in self.servers.items():
            logger.info(f"  • {name}: PID {process.pid}")
        
        # Start monitoring task
        monitor_task = asyncio.create_task(self.monitor_servers())
        
        try:
            # Wait for shutdown signal
            await self.shutdown_event.wait()
        except KeyboardInterrupt:
            pass
        finally:
            # Cancel monitoring
            monitor_task.cancel()
            
            # Stop all servers
            await self.stop_all_servers()
        
        logger.info("MCP Server Manager shutdown complete")
        return 0

async def main():
    """Main entry point."""
    # Ensure directories exist
    Path('/app/logs/mcp_servers').mkdir(parents=True, exist_ok=True)
    Path('/app/papers').mkdir(parents=True, exist_ok=True)
    
    # Create and run server manager
    manager = MCPServerManager()
    return await manager.run()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)