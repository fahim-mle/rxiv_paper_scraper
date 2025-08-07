#!/bin/bash

# Production MCP Server Startup Script for arXiv Scraper
# This script starts all MCP servers in the background with proper logging

set -e

PROJECT_ROOT="/mnt/projects/workspace/rxiv_paper_scraper"
EXTERNAL_SERVERS="$PROJECT_ROOT/external_mcp_servers"
LOG_DIR="$PROJECT_ROOT/logs/mcp_servers"
PID_DIR="$PROJECT_ROOT/logs/pids"

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

echo "=================================================="
echo "Starting MCP Servers for arXiv Scraper"
echo "=================================================="

# Function to start a server and manage its PID
start_server() {
    local server_name="$1"
    local start_command="$2"
    local log_file="$LOG_DIR/${server_name}.log"
    local pid_file="$PID_DIR/${server_name}.pid"
    
    echo "Starting $server_name..."
    
    # Check if server is already running
    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        echo "  ✓ $server_name is already running (PID: $(cat "$pid_file"))"
        return 0
    fi
    
    # Start the server in background
    eval $start_command > "$log_file" 2>&1 &
    local server_pid=$!
    echo $server_pid > "$pid_file"
    
    # Give server time to start
    sleep 3
    
    # Check if server is still running
    if kill -0 $server_pid 2>/dev/null; then
        echo "  ✓ $server_name started successfully (PID: $server_pid)"
        echo "  📊 Logs: $log_file"
    else
        echo "  ✗ $server_name failed to start"
        echo "  📊 Check logs: $log_file"
        return 1
    fi
}

# 1. Start arXiv MCP Server (Port 3001)
echo ""
echo "1. Starting arXiv MCP Server..."
start_server "arxiv" "python -m arxiv_mcp_server --storage-path $PROJECT_ROOT/papers/"

# 2. Start Fetch MCP Server (Port 3004)
echo ""
echo "2. Starting Fetch MCP Server..."
start_server "fetch" "mcp-server-fetch"

# Note: Other servers would require additional setup
echo ""
echo "Note: Additional MCP servers available but require setup:"
echo "  - Playwright (Node.js required)"
echo "  - Unstructured (GPU acceleration recommended)"
echo "  - Tinybird (Database connection required)"
echo "  - PiloTY (SSH configuration required)"

echo ""
echo "=================================================="
echo "MCP Server Startup Complete"
echo "=================================================="
echo ""
echo "Active servers:"
echo "  • arXiv MCP Server    - Running on default port"
echo "  • Fetch MCP Server    - Running on default port"
echo ""
echo "To stop all servers:"
echo "  ./scripts/stop_mcp_servers.sh"
echo ""
echo "To check server status:"
echo "  ./scripts/status_mcp_servers.sh"
echo ""
echo "To test connections:"
echo "  python test_mcp_connections.py"
echo ""
echo "Logs are stored in: $LOG_DIR"
echo "PIDs are stored in: $PID_DIR"
echo "=================================================="