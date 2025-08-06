#!/bin/bash

# Start MongoDB for arXiv Scraper Project
# This script starts MongoDB in user mode without requiring sudo

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
MONGODB_DATA_DIR="/mnt/data/mongodb_user/data"
MONGODB_LOG_FILE="/mnt/data/mongodb_user/logs/mongod.log"
MONGODB_PID_FILE="/mnt/data/mongodb_user/mongod.pid"
MONGODB_PORT="27017"

print_status "Starting MongoDB for arXiv Scraper Project"

# Check if MongoDB is already running
if [ -f "$MONGODB_PID_FILE" ]; then
    PID=$(cat "$MONGODB_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        print_warning "MongoDB is already running (PID: $PID)"
        exit 0
    else
        print_warning "Stale PID file found, removing..."
        rm -f "$MONGODB_PID_FILE"
    fi
fi

# Check if directories exist
if [ ! -d "$MONGODB_DATA_DIR" ] || [ ! -d "$(dirname "$MONGODB_LOG_FILE")" ]; then
    print_error "MongoDB directories not found!"
    print_status "Creating directories..."
    mkdir -p "$MONGODB_DATA_DIR" "$(dirname "$MONGODB_LOG_FILE")"
fi

# Start MongoDB
print_status "Starting MongoDB server..."

mongod \
    --dbpath "$MONGODB_DATA_DIR" \
    --logpath "$MONGODB_LOG_FILE" \
    --port "$MONGODB_PORT" \
    --pidfilepath "$MONGODB_PID_FILE" \
    --fork

if [ $? -eq 0 ]; then
    print_status "MongoDB started successfully"
    
    # Wait a moment and test connection
    sleep 2
    if mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        print_status "MongoDB is accepting connections on port $MONGODB_PORT"
    else
        print_warning "MongoDB started but connection test failed"
    fi
else
    print_error "Failed to start MongoDB"
    exit 1
fi

echo ""
echo "MongoDB Status:"
echo "==============="
echo "Data Directory: $MONGODB_DATA_DIR"
echo "Log File: $MONGODB_LOG_FILE"
echo "PID File: $MONGODB_PID_FILE"
echo "Port: $MONGODB_PORT"
echo ""
echo "To connect: mongosh"
echo "To stop: ./scripts/stop_mongodb.sh"
echo "To check status: ./scripts/status_mongodb.sh"