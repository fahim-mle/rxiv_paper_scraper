#!/bin/bash

# Check MongoDB Status for arXiv Scraper Project
# This script checks the status of the user-mode MongoDB instance

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Configuration
MONGODB_PID_FILE="/mnt/data/mongodb_user/mongod.pid"
MONGODB_LOG_FILE="/mnt/data/mongodb_user/logs/mongod.log"
MONGODB_DATA_DIR="/mnt/data/mongodb_user/data"

print_header "MongoDB Status Check - arXiv Scraper Project"
print_header "=============================================="

# Check if MongoDB is running via PID file
if [ -f "$MONGODB_PID_FILE" ]; then
    PID=$(cat "$MONGODB_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        print_status "Status: RUNNING (PID: $PID)"
        MONGODB_RUNNING=true
    else
        print_warning "Status: NOT RUNNING (stale PID file)"
        rm -f "$MONGODB_PID_FILE"
        MONGODB_RUNNING=false
    fi
else
    # Check for any mongod processes
    if pgrep -x mongod >/dev/null; then
        MONGOD_PIDS=$(pgrep -x mongod | tr '\n' ' ')
        print_warning "Status: RUNNING (no PID file, PIDs: $MONGOD_PIDS)"
        MONGODB_RUNNING=true
    else
        print_error "Status: NOT RUNNING"
        MONGODB_RUNNING=false
    fi
fi

echo ""

# Test connection if running
if [ "$MONGODB_RUNNING" = true ]; then
    print_header "Connection Test:"
    if mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        print_status "Connection: OK"
        
        # Get database statistics
        echo ""
        print_header "Database Statistics:"
        mongosh --quiet --eval "
            const stats = db.runCommand({listCollections: 1});
            print('Collections: ' + stats.cursor.firstBatch.length);
            const dbStats = db.stats();
            print('Data Size: ' + (dbStats.dataSize / 1024 / 1024).toFixed(2) + ' MB');
            print('Storage Size: ' + (dbStats.storageSize / 1024 / 1024).toFixed(2) + ' MB');
            print('Indexes: ' + dbStats.indexes);
        " 2>/dev/null || print_warning "Could not retrieve database statistics"
    else
        print_error "Connection: FAILED"
    fi
fi

echo ""
print_header "System Information:"
print_status "Data Directory: $MONGODB_DATA_DIR"
print_status "Log File: $MONGODB_LOG_FILE"
print_status "PID File: $MONGODB_PID_FILE"

# Show disk usage
if command -v df >/dev/null 2>&1; then
    echo ""
    print_header "Disk Usage:"
    df -h /mnt/data 2>/dev/null | grep -E "(Filesystem|/mnt/data)" || print_warning "Cannot check disk usage for /mnt/data"
fi

# Show recent log entries if log file exists
if [ -f "$MONGODB_LOG_FILE" ]; then
    echo ""
    print_header "Recent Log Entries (last 5):"
    tail -5 "$MONGODB_LOG_FILE" | while read -r line; do
        # Extract timestamp and message from MongoDB JSON log format
        if echo "$line" | grep -q '"t":'; then
            TIMESTAMP=$(echo "$line" | grep -o '"t":{"$date":"[^"]*"' | cut -d'"' -f6 | cut -d'T' -f2 | cut -d'.' -f1)
            LEVEL=$(echo "$line" | grep -o '"s":"[^"]*"' | cut -d'"' -f4)
            MSG=$(echo "$line" | grep -o '"msg":"[^"]*"' | cut -d'"' -f4)
            echo "[$TIMESTAMP] $LEVEL: $MSG"
        else
            echo "$line"
        fi
    done 2>/dev/null || print_warning "Could not read recent log entries"
fi

echo ""
print_header "Control Commands:"
if [ "$MONGODB_RUNNING" = true ]; then
    print_status "To stop: ./scripts/stop_mongodb.sh"
    print_status "To connect: mongosh"
else
    print_status "To start: ./scripts/start_mongodb.sh"
fi