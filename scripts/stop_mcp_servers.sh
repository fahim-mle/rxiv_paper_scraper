#!/bin/bash

# Production MCP Server Stop Script for arXiv Scraper
# This script gracefully stops all running MCP servers

set -e

PROJECT_ROOT="/mnt/projects/workspace/rxiv_paper_scraper"
PID_DIR="$PROJECT_ROOT/logs/pids"
LOG_DIR="$PROJECT_ROOT/logs/mcp_servers"

echo "=================================================="
echo "Stopping MCP Servers for arXiv Scraper"
echo "=================================================="

# Function to stop a server by name
stop_server() {
    local server_name="$1"
    local pid_file="$PID_DIR/${server_name}.pid"
    
    echo "Stopping $server_name..."
    
    if [ ! -f "$pid_file" ]; then
        echo "  ℹ No PID file found for $server_name"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "  ℹ $server_name not running (stale PID file removed)"
        rm -f "$pid_file"
        return 0
    fi
    
    # Try graceful shutdown first
    echo "  🔄 Sending SIGTERM to $server_name (PID: $pid)..."
    kill -TERM "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        echo "  🔥 Force killing $server_name..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi
    
    # Verify and clean up
    if kill -0 "$pid" 2>/dev/null; then
        echo "  ✗ Failed to stop $server_name"
        return 1
    else
        echo "  ✓ $server_name stopped successfully"
        rm -f "$pid_file"
        return 0
    fi
}

# Stop all known servers
servers=("arxiv" "fetch" "playwright" "unstructured" "tinybird" "piloty")

for server in "${servers[@]}"; do
    echo ""
    stop_server "$server"
done

# Kill any remaining MCP processes
echo ""
echo "Checking for remaining MCP processes..."
remaining_pids=$(pgrep -f "mcp.*server" 2>/dev/null || true)
if [ -n "$remaining_pids" ]; then
    echo "Found remaining MCP processes: $remaining_pids"
    echo "Stopping remaining processes..."
    echo $remaining_pids | xargs kill -TERM 2>/dev/null || true
    sleep 2
    echo $remaining_pids | xargs kill -KILL 2>/dev/null || true
fi

echo ""
echo "=================================================="
echo "MCP Server Shutdown Complete"
echo "=================================================="
echo ""
echo "All MCP servers have been stopped."
echo "Logs preserved in: $LOG_DIR"
echo ""
echo "To restart servers:"
echo "  ./scripts/start_mcp_servers.sh"
echo ""
echo "=================================================="