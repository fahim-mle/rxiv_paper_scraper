#!/bin/bash

# Setup script for MCP servers for arXiv Scraper Project
# This script clones and sets up the required MCP servers

set -e

echo "=================================================="
echo "arXiv Scraper MCP Server Setup"
echo "=================================================="

# Create directories for external MCP servers
mkdir -p external_mcp_servers
cd external_mcp_servers

echo "Setting up MCP servers..."

# 1. arXiv MCP Server
echo "1. Setting up arXiv MCP Server..."
if [ ! -d "arxiv-mcp-server" ]; then
    git clone https://github.com/blazickjp/arxiv-mcp-server.git
    cd arxiv-mcp-server
    pip install -r requirements.txt 2>/dev/null || pip install arxiv requests
    cd ..
    echo "   ✓ arXiv MCP Server cloned and set up"
else
    echo "   ✓ arXiv MCP Server already exists"
fi

# 2. MCP Servers (Official)
echo "2. Setting up official MCP servers (Playwright, Fetch)..."
if [ ! -d "servers" ]; then
    git clone https://github.com/modelcontextprotocol/servers.git
    cd servers
    
    # Install Node.js dependencies for Playwright
    if command -v npm &> /dev/null; then
        cd src/playwright
        npm install 2>/dev/null || echo "   ⚠ npm install failed for playwright - install Node.js"
        cd ../..
    else
        echo "   ⚠ npm not found - install Node.js for Playwright support"
    fi
    
    cd ..
    echo "   ✓ Official MCP servers cloned"
else
    echo "   ✓ Official MCP servers already exist"
fi

# 3. Unstructured
echo "3. Setting up Unstructured..."
pip install "unstructured[all-docs]" 2>/dev/null || pip install unstructured
echo "   ✓ Unstructured installed"

# 4. Tinybird MCP Server
echo "4. Setting up Tinybird MCP Server..."
if [ ! -d "mcp-server" ]; then
    git clone https://github.com/tinybirdco/mcp-server.git
    cd mcp-server
    pip install -r requirements.txt 2>/dev/null || pip install requests clickhouse-connect
    cd ..
    echo "   ✓ Tinybird MCP Server cloned and set up"
else
    echo "   ✓ Tinybird MCP Server already exists"
fi

# 5. PiloTY MCP Server
echo "5. Setting up PiloTY MCP Server..."
if [ ! -d "piloty" ]; then
    git clone https://github.com/pilotymcp/piloty.git
    cd piloty
    pip install -r requirements.txt 2>/dev/null || pip install paramiko psutil schedule
    cd ..
    echo "   ✓ PiloTY MCP Server cloned and set up"
else
    echo "   ✓ PiloTY MCP Server already exists"
fi

cd ..

echo ""
echo "=================================================="
echo "MCP Server Setup Complete!"
echo "=================================================="
echo ""
echo "To start the MCP servers, run the following commands:"
echo ""
echo "1. arXiv MCP Server (Port 3001):"
echo "   cd external_mcp_servers/arxiv-mcp-server"
echo "   python server.py --port 3001 --storage-path ../papers/"
echo ""
echo "2. Playwright MCP Server (Port 3002):"
echo "   cd external_mcp_servers/servers/src/playwright"
echo "   node index.js --port 3002"
echo ""
echo "3. Fetch MCP Server (Port 3004):"
echo "   cd external_mcp_servers/servers/src/fetch"
echo "   node index.js --port 3004"
echo ""
echo "4. Tinybird MCP Server (Port 3005):"
echo "   cd external_mcp_servers/mcp-server"
echo "   python server.py --port 3005"
echo ""
echo "5. PiloTY MCP Server (Port 3006):"
echo "   cd external_mcp_servers/piloty"
echo "   python server.py --port 3006"
echo ""
echo "Note: Unstructured (Port 3003) can be run as a service or integrated directly."
echo ""
echo "After starting the servers, run: python test_mcp_connections.py"
echo "=================================================="