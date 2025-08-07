#!/bin/bash

# Production MCP Server Status Script for arXiv Scraper
# This script checks the status of all MCP servers

set -e

PROJECT_ROOT="/mnt/projects/workspace/rxiv_paper_scraper"
PID_DIR="$PROJECT_ROOT/logs/pids"
LOG_DIR="$PROJECT_ROOT/logs/mcp_servers"

echo "=================================================="
echo "MCP Server Status for arXiv Scraper"
echo "=================================================="

# Function to check server status
check_server_status() {
    local server_name="$1"
    local expected_port="$2"
    local pid_file="$PID_DIR/${server_name}.pid"
    local log_file="$LOG_DIR/${server_name}.log"
    
    printf "%-12s | " "$server_name"
    
    if [ ! -f "$pid_file" ]; then
        printf "%-10s | %-6s | %s\n" "STOPPED" "N/A" "No PID file"
        return 1
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! kill -0 "$pid" 2>/dev/null; then
        printf "%-10s | %-6s | %s\n" "DEAD" "N/A" "Stale PID file"
        rm -f "$pid_file"
        return 1
    fi
    
    # Get process info
    local cpu_mem=$(ps -p "$pid" -o %cpu,%mem --no-headers 2>/dev/null | tr -s ' ')
    local uptime=$(ps -p "$pid" -o etime --no-headers 2>/dev/null | tr -s ' ')
    
    # Check if port is open (if specified)
    local port_status="N/A"
    if [ -n "$expected_port" ]; then
        if netstat -tuln 2>/dev/null | grep -q ":$expected_port "; then
            port_status="OPEN"
        else
            port_status="CLOSED"
        fi
    fi
    
    printf "%-10s | %-6s | PID: %-6s | Uptime: %-8s | CPU/Mem: %s\n" "RUNNING" "$port_status" "$pid" "$uptime" "$cpu_mem"
    
    # Show recent log activity
    if [ -f "$log_file" ] && [ -s "$log_file" ]; then
        local recent_logs=$(tail -1 "$log_file" 2>/dev/null | cut -c1-60)
        if [ -n "$recent_logs" ]; then
            printf "%-12s | %-10s | %-6s | Last log: %s...\n" "" "" "" "$recent_logs"
        fi
    fi
    
    return 0
}

# Header
printf "%-12s | %-10s | %-6s | %s\n" "SERVER" "STATUS" "PORT" "DETAILS"
printf "%-12s-|-%-10s-|-%-6s-|-%s\n" "------------" "----------" "------" "----------------------------------------"

# Check all known servers
check_server_status "arxiv" ""
check_server_status "fetch" ""
check_server_status "playwright" "3002"
check_server_status "unstructured" "3003"
check_server_status "tinybird" "3005"
check_server_status "piloty" "3006"

echo ""
echo "=================================================="
echo "System Resources"
echo "=================================================="

# Show system load
echo "System Load:"
uptime

echo ""
echo "Memory Usage:"
free -h | head -2

echo ""
echo "Disk Usage (arXiv papers directory):"
if [ -d "$PROJECT_ROOT/papers" ]; then
    du -sh "$PROJECT_ROOT/papers" 2>/dev/null || echo "Papers directory not found"
else
    echo "Papers directory not created yet"
fi

echo ""
echo "Network Connections (MCP related):"
netstat -tuln 2>/dev/null | grep -E ":(300[0-9]|800[0-9])" || echo "No MCP servers listening on standard ports"

echo ""
echo "=================================================="
echo "Quick Actions"
echo "=================================================="
echo "Start all servers:    ./scripts/start_mcp_servers.sh"
echo "Stop all servers:     ./scripts/stop_mcp_servers.sh"
echo "Test connections:     python test_mcp_connections.py"
echo "View server logs:     ls -la $LOG_DIR"
echo "=================================================="