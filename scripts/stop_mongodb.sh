#!/bin/bash

# Stop MongoDB for arXiv Scraper Project
# This script stops the user-mode MongoDB instance

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Configuration
MONGODB_PID_FILE="/mnt/data/mongodb_user/mongod.pid"

print_status "Stopping MongoDB for arXiv Scraper Project"

# Check if PID file exists
if [ -f "$MONGODB_PID_FILE" ]; then
    PID=$(cat "$MONGODB_PID_FILE")
    
    # Check if process is running
    if kill -0 "$PID" 2>/dev/null; then
        print_status "Stopping MongoDB (PID: $PID)..."
        
        # Send SIGTERM for graceful shutdown
        kill "$PID"
        
        # Wait for process to stop
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                print_status "MongoDB stopped successfully"
                rm -f "$MONGODB_PID_FILE"
                break
            fi
            
            if [ $i -eq 10 ]; then
                print_warning "MongoDB didn't stop gracefully, forcing shutdown..."
                kill -9 "$PID" 2>/dev/null || true
                rm -f "$MONGODB_PID_FILE"
                print_status "MongoDB force-stopped"
            else
                sleep 1
            fi
        done
    else
        print_warning "PID file exists but process not running"
        rm -f "$MONGODB_PID_FILE"
    fi
else
    # Try to find and kill any mongod processes
    if pgrep -x mongod >/dev/null; then
        print_warning "Found mongod processes without PID file"
        pkill -x mongod
        print_status "MongoDB processes terminated"
    else
        print_status "No MongoDB processes found"
    fi
fi

# Verify it's stopped
if pgrep -x mongod >/dev/null; then
    print_error "MongoDB processes still running after shutdown attempt"
    exit 1
else
    print_status "MongoDB shutdown complete"
fi