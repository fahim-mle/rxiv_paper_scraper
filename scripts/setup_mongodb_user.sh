#!/bin/bash

# MongoDB User Setup Script for arXiv Scraper Project
# This script sets up MongoDB without requiring sudo access

set -e  # Exit on any error

echo "MongoDB User Setup for arXiv Scraper Project"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_action() {
    echo -e "${BLUE}[ACTION]${NC} $1"
}

# Configuration
PROJECT_ROOT="/mnt/projects/workspace/rxiv_paper_scraper"
MONGODB_DATA_DIR="/mnt/data/mongodb"
ARXIV_DATA_DIR="/mnt/data/arxiv_papers"
USER_MONGODB_CONFIG="$PROJECT_ROOT/mongodb_user.conf"
CURRENT_USER=$(whoami)

print_status "Setting up MongoDB for user: $CURRENT_USER"

# Step 1: Check if we can create directories on /mnt/data
print_status "Checking /mnt/data directory permissions..."

if [ ! -d "/mnt/data" ]; then
    print_error "/mnt/data directory does not exist."
    print_action "Please run as root first: mkdir -p /mnt/data && chown $CURRENT_USER:$CURRENT_USER /mnt/data"
    exit 1
fi

# Try to create a test directory
if mkdir -p /mnt/data/test_write 2>/dev/null; then
    rmdir /mnt/data/test_write
    print_status "/mnt/data is writable by current user"
    CAN_WRITE_MNT_DATA=true
else
    print_warning "/mnt/data is not writable by current user"
    CAN_WRITE_MNT_DATA=false
fi

# Step 2: Create MongoDB directories
if [ "$CAN_WRITE_MNT_DATA" = true ]; then
    print_status "Creating MongoDB directories..."
    
    mkdir -p $MONGODB_DATA_DIR/data
    mkdir -p $MONGODB_DATA_DIR/logs
    mkdir -p $ARXIV_DATA_DIR/papers
    mkdir -p $ARXIV_DATA_DIR/books
    mkdir -p $ARXIV_DATA_DIR/articles
    mkdir -p $ARXIV_DATA_DIR/temp
    
    # Set proper permissions (if possible)
    chmod -R 755 $MONGODB_DATA_DIR 2>/dev/null || print_warning "Could not set permissions on $MONGODB_DATA_DIR"
    chmod -R 755 $ARXIV_DATA_DIR 2>/dev/null || print_warning "Could not set permissions on $ARXIV_DATA_DIR"
    
    print_status "Directories created successfully"
else
    print_error "Cannot create directories in /mnt/data"
    print_action "Please run as root:"
    echo "  mkdir -p $MONGODB_DATA_DIR/{data,logs}"
    echo "  mkdir -p $ARXIV_DATA_DIR/{papers,books,articles,temp}"
    echo "  chown -R $CURRENT_USER:$CURRENT_USER /mnt/data"
    echo "  chmod -R 755 /mnt/data"
    echo ""
    print_action "Then re-run this script"
    exit 1
fi

# Step 3: Create user MongoDB configuration
print_status "Creating user MongoDB configuration..."

cat > $USER_MONGODB_CONFIG << EOF
# MongoDB Configuration for arXiv Scraper Project (User Mode)
# Optimized for academic paper metadata storage on /mnt/data

# Network settings
net:
  port: 27017
  bindIp: 127.0.0.1,::1
  maxIncomingConnections: 100

# Storage settings - using /mnt/data for data directory
storage:
  dbPath: $MONGODB_DATA_DIR/data
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2  # Adjust based on available RAM
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

# System logging
systemLog:
  destination: file
  path: $MONGODB_DATA_DIR/logs/mongod.log
  logAppend: true
  logRotate: rename

# Process management
processManagement:
  fork: true
  pidFilePath: $MONGODB_DATA_DIR/mongod.pid

# Security settings (disabled for user mode)
# security:
#   authorization: enabled

# Operation profiling for performance monitoring
operationProfiling:
  slowOpThresholdMs: 100
  mode: slowOp

# Replication (disabled for single instance)
# replication:
#   replSetName: "arxiv-scraper-rs"

# Sharding (disabled for single instance)
# sharding:
#   clusterRole: configsvr
EOF

print_status "MongoDB configuration created at: $USER_MONGODB_CONFIG"

# Step 4: Check if MongoDB is installed
print_status "Checking MongoDB installation..."

if command -v mongod >/dev/null 2>&1; then
    MONGOD_VERSION=$(mongod --version | head -1)
    print_status "MongoDB found: $MONGOD_VERSION"
else
    print_error "MongoDB is not installed!"
    print_action "Install MongoDB first:"
    echo "  # Ubuntu/Debian:"
    echo "  wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -"
    echo "  echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse' | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y mongodb-org"
    echo ""
    echo "  # Or using snap:"
    echo "  sudo snap install mongodb"
    exit 1
fi

# Step 5: Check if MongoDB is already running
print_status "Checking if MongoDB is already running..."

if pgrep -f "mongod --config" >/dev/null || pgrep -x mongod >/dev/null; then
    print_warning "MongoDB server is already running. Stopping existing instance..."
    pkill -f "mongod --config" || pkill -x mongod || true
    sleep 3
fi

# Step 6: Start MongoDB with user configuration
print_status "Starting MongoDB with user configuration..."

# Create startup script
MONGODB_STARTUP_SCRIPT="$PROJECT_ROOT/scripts/start_mongodb_user.sh"
cat > $MONGODB_STARTUP_SCRIPT << EOF
#!/bin/bash
# MongoDB startup script for user mode

MONGODB_CONFIG="$USER_MONGODB_CONFIG"
MONGODB_PID="$MONGODB_DATA_DIR/mongod.pid"

echo "Starting MongoDB with config: \$MONGODB_CONFIG"

# Remove old pid file if it exists
if [ -f "\$MONGODB_PID" ]; then
    rm "\$MONGODB_PID"
fi

# Start MongoDB
mongod --config "\$MONGODB_CONFIG"
EOF

chmod +x $MONGODB_STARTUP_SCRIPT

# Start MongoDB
print_status "Starting MongoDB..."
if $MONGODB_STARTUP_SCRIPT; then
    print_status "MongoDB startup initiated"
else
    print_error "Failed to start MongoDB"
    exit 1
fi

# Step 7: Wait for MongoDB to be ready
print_status "Waiting for MongoDB to be ready..."
sleep 5

# Test MongoDB connection
for i in {1..10}; do
    if mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        print_status "MongoDB is running and accepting connections"
        break
    elif [ $i -eq 10 ]; then
        print_error "MongoDB is not responding to connections after 10 attempts"
        print_error "Check logs: tail -f $MONGODB_DATA_DIR/logs/mongod.log"
        exit 1
    else
        print_status "Attempt $i/10: Waiting for MongoDB..."
        sleep 2
    fi
done

# Step 8: Create MongoDB management scripts
print_status "Creating MongoDB management scripts..."

# Stop script
cat > "$PROJECT_ROOT/scripts/stop_mongodb_user.sh" << 'EOF'
#!/bin/bash
# Stop MongoDB user instance

MONGODB_PID="/mnt/data/mongodb/mongod.pid"

echo "Stopping MongoDB..."

if [ -f "$MONGODB_PID" ]; then
    PID=$(cat "$MONGODB_PID")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "MongoDB stopped (PID: $PID)"
        rm -f "$MONGODB_PID"
    else
        echo "MongoDB PID file exists but process not running"
        rm -f "$MONGODB_PID"
    fi
else
    # Try to find and kill any mongod processes
    if pgrep -f mongod >/dev/null; then
        pkill -f mongod
        echo "MongoDB processes terminated"
    else
        echo "No MongoDB processes found"
    fi
fi
EOF

# Status script
cat > "$PROJECT_ROOT/scripts/status_mongodb_user.sh" << 'EOF'
#!/bin/bash
# Check MongoDB user instance status

MONGODB_PID="/mnt/data/mongodb/mongod.pid"
MONGODB_LOG="/mnt/data/mongodb/logs/mongod.log"

echo "MongoDB Status Check"
echo "===================="

if [ -f "$MONGODB_PID" ]; then
    PID=$(cat "$MONGODB_PID")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Status: RUNNING (PID: $PID)"
        
        # Test connection
        if mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
            echo "Connection: OK"
            
            # Get basic stats
            echo ""
            echo "Database Stats:"
            mongosh --quiet --eval "
                const stats = db.adminCommand('listCollections');
                print('Collections: ' + stats.cursor.firstBatch.length);
                const dbStats = db.stats();
                print('Data Size: ' + (dbStats.dataSize / 1024 / 1024).toFixed(2) + ' MB');
                print('Storage Size: ' + (dbStats.storageSize / 1024 / 1024).toFixed(2) + ' MB');
            "
        else
            echo "Connection: FAILED"
        fi
    else
        echo "Status: NOT RUNNING (stale PID file)"
        rm -f "$MONGODB_PID"
    fi
else
    if pgrep -f mongod >/dev/null; then
        echo "Status: RUNNING (no PID file)"
    else
        echo "Status: NOT RUNNING"
    fi
fi

echo ""
echo "Data Directory: /mnt/data/mongodb/data"
echo "Log File: $MONGODB_LOG"

if [ -f "$MONGODB_LOG" ]; then
    echo ""
    echo "Recent Log Entries:"
    echo "==================="
    tail -5 "$MONGODB_LOG"
fi

echo ""
echo "Disk Usage:"
echo "==========="
df -h /mnt/data 2>/dev/null || echo "Cannot check /mnt/data disk usage"
EOF

chmod +x "$PROJECT_ROOT/scripts/stop_mongodb_user.sh"
chmod +x "$PROJECT_ROOT/scripts/status_mongodb_user.sh"

# Step 9: Display setup summary
print_status "MongoDB user setup completed successfully!"

echo ""
echo "Setup Summary:"
echo "=============="
echo "MongoDB Data: $MONGODB_DATA_DIR/data"
echo "MongoDB Logs: $MONGODB_DATA_DIR/logs/mongod.log"
echo "Storage Dir:  $ARXIV_DATA_DIR"
echo "Config File:  $USER_MONGODB_CONFIG"
echo ""

echo "Management Commands:"
echo "==================="
echo "Start:   $PROJECT_ROOT/scripts/start_mongodb_user.sh"
echo "Stop:    $PROJECT_ROOT/scripts/stop_mongodb_user.sh" 
echo "Status:  $PROJECT_ROOT/scripts/status_mongodb_user.sh"
echo ""

echo "Connection:"
echo "==========="
echo "mongosh"
echo "mongosh --eval 'db.stats()'"
echo ""

# Check disk space
echo "Disk Usage:"
echo "==========="
df -h /mnt/data 2>/dev/null || echo "Cannot check /mnt/data disk usage"

echo ""
echo "Next Steps:"
echo "==========="
echo "1. Initialize the database:"
echo "   cd $PROJECT_ROOT"
echo "   python scripts/init_mongodb.py"
echo ""
echo "2. Test the setup:"
echo "   python scripts/db_health_check.py"
echo ""
echo "3. Start the arXiv scraper:"
echo "   python main.py"
echo ""

print_status "MongoDB is ready for the arXiv scraper project!"