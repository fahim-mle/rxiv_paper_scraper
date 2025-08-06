"""
Multi-Agent Database Connection Pool Manager

Manages database connections for multiple agents in the arXiv scraper system,
ensuring efficient resource usage and preventing connection exhaustion.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from contextlib import contextmanager
from pymongo import MongoClient
from pymongo.database import Database
from .mongodb_connector import MongoDBConnector
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AgentConnectionInfo:
    """Information about an agent's database connection usage."""
    agent_id: str
    agent_type: str  # crawler, scraper, downloader, nlp, etc.
    connection_count: int = 0
    last_activity: float = 0
    max_connections: int = 5
    priority: int = 1  # Higher priority gets preference during resource contention


class AgentPoolManager:
    """
    Connection pool manager optimized for multi-agent access patterns.
    
    Manages database connections across different agent types with:
    - Per-agent connection limits
    - Priority-based resource allocation
    - Connection health monitoring
    - Automatic cleanup of idle connections
    """
    
    def __init__(self, 
                 total_max_connections: int = 50,
                 cleanup_interval_seconds: int = 300,
                 connection_timeout_seconds: int = 1800):
        """
        Initialize the agent pool manager.
        
        Args:
            total_max_connections: Maximum total connections across all agents
            cleanup_interval_seconds: How often to clean up idle connections
            connection_timeout_seconds: How long before idle connections are closed
        """
        self.settings = get_settings()
        self.total_max_connections = total_max_connections
        self.cleanup_interval = cleanup_interval_seconds
        self.connection_timeout = connection_timeout_seconds
        
        # Thread-safe data structures
        self._lock = threading.RLock()
        self._agents: Dict[str, AgentConnectionInfo] = {}
        self._connections: Dict[str, Dict[str, MongoClient]] = {}
        self._active_connections = 0
        
        # Background cleanup thread
        self._cleanup_thread = None
        self._shutdown = False
        
        # Agent type configurations
        self._agent_configs = {
            "crawler": {"max_connections": 8, "priority": 2},
            "scraper": {"max_connections": 10, "priority": 3},
            "downloader": {"max_connections": 5, "priority": 2},
            "database": {"max_connections": 3, "priority": 4},
            "nlp": {"max_connections": 4, "priority": 1},
            "monitoring": {"max_connections": 2, "priority": 1},
            "testing": {"max_connections": 2, "priority": 1},
            "orchestrator": {"max_connections": 3, "priority": 4},
        }
        
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self._cleanup_thread.start()
    
    def _cleanup_worker(self):
        """Background worker to clean up idle connections."""
        while not self._shutdown:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_idle_connections()
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
    
    def _cleanup_idle_connections(self):
        """Clean up idle connections that have exceeded timeout."""
        current_time = time.time()
        
        with self._lock:
            for agent_id in list(self._agents.keys()):
                agent_info = self._agents[agent_id]
                
                # Check if agent has been idle too long
                if current_time - agent_info.last_activity > self.connection_timeout:
                    logger.info(f"Cleaning up idle connections for agent {agent_id}")
                    self._close_agent_connections(agent_id)
    
    def _close_agent_connections(self, agent_id: str):
        """Close all connections for a specific agent."""
        if agent_id in self._connections:
            for conn_id, client in self._connections[agent_id].items():
                try:
                    client.close()
                    self._active_connections -= 1
                    logger.debug(f"Closed connection {conn_id} for agent {agent_id}")
                except Exception as e:
                    logger.error(f"Error closing connection for agent {agent_id}: {e}")
            
            del self._connections[agent_id]
        
        if agent_id in self._agents:
            del self._agents[agent_id]
    
    def register_agent(self, 
                      agent_id: str, 
                      agent_type: str,
                      max_connections: Optional[int] = None,
                      priority: Optional[int] = None) -> bool:
        """
        Register an agent with the pool manager.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (crawler, scraper, etc.)
            max_connections: Maximum connections for this agent
            priority: Priority level (higher = more important)
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            with self._lock:
                if agent_id in self._agents:
                    logger.warning(f"Agent {agent_id} already registered")
                    return False
                
                # Get configuration for agent type
                type_config = self._agent_configs.get(agent_type, {})
                max_conn = max_connections or type_config.get("max_connections", 3)
                agent_priority = priority or type_config.get("priority", 1)
                
                agent_info = AgentConnectionInfo(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    max_connections=max_conn,
                    priority=agent_priority,
                    last_activity=time.time()
                )
                
                self._agents[agent_id] = agent_info
                self._connections[agent_id] = {}
                
                logger.info(f"Registered agent {agent_id} ({agent_type}) with {max_conn} max connections")
                return True
                
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    def _can_create_connection(self, agent_id: str) -> bool:
        """Check if an agent can create a new connection."""
        agent_info = self._agents.get(agent_id)
        if not agent_info:
            return False
        
        # Check agent-specific limits
        if agent_info.connection_count >= agent_info.max_connections:
            return False
        
        # Check global limits
        if self._active_connections >= self.total_max_connections:
            # Try to free up connections from lower priority agents
            return self._try_free_connections_for_agent(agent_id)
        
        return True
    
    def _try_free_connections_for_agent(self, requesting_agent_id: str) -> bool:
        """Try to free connections from lower priority agents."""
        requesting_agent = self._agents.get(requesting_agent_id)
        if not requesting_agent:
            return False
        
        # Find agents with lower priority and idle connections
        candidates = []
        for agent_id, agent_info in self._agents.items():
            if (agent_id != requesting_agent_id and 
                agent_info.priority < requesting_agent.priority and
                agent_info.connection_count > 1):  # Keep at least one connection
                candidates.append((agent_id, agent_info))
        
        # Sort by priority (lowest first) and last activity (oldest first)
        candidates.sort(key=lambda x: (x[1].priority, x[1].last_activity))
        
        # Close one connection from the lowest priority agent
        if candidates:
            agent_id, _ = candidates[0]
            connections = self._connections.get(agent_id, {})
            if connections:
                # Close the first connection
                conn_id = next(iter(connections))
                client = connections[conn_id]
                try:
                    client.close()
                    del connections[conn_id]
                    self._agents[agent_id].connection_count -= 1
                    self._active_connections -= 1
                    logger.info(f"Freed connection from agent {agent_id} for {requesting_agent_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error freeing connection: {e}")
        
        return False
    
    @contextmanager
    def get_connection(self, agent_id: str):
        """
        Context manager to get a database connection for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Yields:
            Database instance
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not registered")
        
        connection_id = f"{agent_id}_{threading.current_thread().ident}_{time.time()}"
        client = None
        
        try:
            with self._lock:
                if not self._can_create_connection(agent_id):
                    raise RuntimeError(f"Cannot create connection for agent {agent_id}")
                
                # Create new connection
                connector = MongoDBConnector(
                    username=self.settings.database.username,
                    password=self.settings.database.password,
                    max_pool_size=5,  # Smaller pool per connection
                    min_pool_size=1
                )
                
                database = connector.connect()
                client = connector._client
                
                # Track the connection
                self._connections[agent_id][connection_id] = client
                self._agents[agent_id].connection_count += 1
                self._agents[agent_id].last_activity = time.time()
                self._active_connections += 1
                
                logger.debug(f"Created connection {connection_id} for agent {agent_id}")
            
            # Yield the database to the agent
            yield database
            
        except Exception as e:
            logger.error(f"Error getting connection for agent {agent_id}: {e}")
            raise
        
        finally:
            # Clean up the connection
            if client:
                try:
                    with self._lock:
                        if (agent_id in self._connections and 
                            connection_id in self._connections[agent_id]):
                            client.close()
                            del self._connections[agent_id][connection_id]
                            self._agents[agent_id].connection_count -= 1
                            self._active_connections -= 1
                            logger.debug(f"Closed connection {connection_id} for agent {agent_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up connection: {e}")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current status of the connection pool."""
        with self._lock:
            agent_status = {}
            for agent_id, agent_info in self._agents.items():
                agent_status[agent_id] = {
                    "type": agent_info.agent_type,
                    "connections": agent_info.connection_count,
                    "max_connections": agent_info.max_connections,
                    "priority": agent_info.priority,
                    "last_activity": agent_info.last_activity,
                    "idle_time": time.time() - agent_info.last_activity
                }
            
            return {
                "total_connections": self._active_connections,
                "max_connections": self.total_max_connections,
                "registered_agents": len(self._agents),
                "agents": agent_status
            }
    
    def shutdown(self):
        """Shutdown the pool manager and close all connections."""
        logger.info("Shutting down agent pool manager")
        self._shutdown = True
        
        with self._lock:
            # Close all connections
            for agent_id in list(self._agents.keys()):
                self._close_agent_connections(agent_id)
            
            self._agents.clear()
            self._connections.clear()
            self._active_connections = 0
        
        # Wait for cleanup thread to finish
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        
        logger.info("Agent pool manager shutdown complete")


# Global pool manager instance
_pool_manager: Optional[AgentPoolManager] = None


def get_agent_pool_manager() -> AgentPoolManager:
    """Get the global agent pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        settings = get_settings()
        _pool_manager = AgentPoolManager(
            total_max_connections=settings.database.max_pool_size
        )
    return _pool_manager


def register_agent(agent_id: str, agent_type: str) -> bool:
    """Register an agent with the pool manager."""
    return get_agent_pool_manager().register_agent(agent_id, agent_type)


@contextmanager
def get_agent_connection(agent_id: str):
    """Get a database connection for an agent."""
    with get_agent_pool_manager().get_connection(agent_id) as db:
        yield db


def shutdown_pool_manager():
    """Shutdown the global pool manager."""
    global _pool_manager
    if _pool_manager:
        _pool_manager.shutdown()
        _pool_manager = None