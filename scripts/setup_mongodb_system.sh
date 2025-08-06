#!/bin/bash

# MongoDB System Setup Script for arXiv Scraper Project
# This script handles system-level MongoDB configuration that requires sudo access

set -e  # Exit on any error

echo "MongoDB System Setup for arXiv Scraper Project"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root. This script should be run with sudo for specific commands only."
fi

# Step 1: Create MongoDB data and log directories
print_status "Creating MongoDB directories on /mnt/data..."

sudo mkdir -p /mnt/data/mongodb/data
sudo mkdir -p /mnt/data/mongodb/logs
sudo mkdir -p /mnt/data/arxiv_papers/papers
sudo mkdir -p /mnt/data/arxiv_papers/books
sudo mkdir -p /mnt/data/arxiv_papers/articles
sudo mkdir -p /mnt/data/arxiv_papers/temp

# Set ownership to mongodb user
if id "mongodb" &>/dev/null; then
    print_status "Setting ownership to mongodb user..."
    sudo chown -R mongodb:mongodb /mnt/data/mongodb
    sudo chmod -R 755 /mnt/data/mongodb
else
    print_warning "mongodb user doesn't exist. Creating with restricted shell..."
    sudo useradd -r -s /bin/false mongodb
    sudo chown -R mongodb:mongodb /mnt/data/mongodb
    sudo chmod -R 755 /mnt/data/mongodb
fi

# Set ownership for arxiv_papers to current user
CURRENT_USER=$(whoami)
sudo chown -R $CURRENT_USER:$CURRENT_USER /mnt/data/arxiv_papers
sudo chmod -R 755 /mnt/data/arxiv_papers

# Step 2: Copy MongoDB configuration file
print_status "Installing MongoDB configuration..."

if [ -f "mongodb.conf" ]; then
    sudo cp mongodb.conf /etc/mongod.conf
    sudo chown root:root /etc/mongod.conf
    sudo chmod 644 /etc/mongod.conf
    print_status "MongoDB configuration installed to /etc/mongod.conf"
else
    print_error "mongodb.conf not found in current directory"
    exit 1
fi

# Step 3: Create systemd service override for custom data path
print_status "Creating systemd service override..."

sudo mkdir -p /etc/systemd/system/mongod.service.d
sudo cat > /etc/systemd/system/mongod.service.d/override.conf << EOF
[Service]
# Override for custom data path and configuration
ExecStart=
ExecStart=/usr/bin/mongod --config /etc/mongod.conf

# Security enhancements
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/mnt/data/mongodb
EOF

# Step 4: Reload systemd and enable MongoDB
print_status "Reloading systemd and enabling MongoDB..."

sudo systemctl daemon-reload
sudo systemctl enable mongod

# Step 5: Start MongoDB service
print_status "Starting MongoDB service..."

if sudo systemctl start mongod; then
    print_status "MongoDB started successfully"
else
    print_error "Failed to start MongoDB"
    print_error "Check logs with: sudo journalctl -u mongod -f"
    exit 1
fi

# Step 6: Wait for MongoDB to be ready
print_status "Waiting for MongoDB to be ready..."
sleep 5

# Test MongoDB connection
if mongosh --eval "db.adminCommand('ping')" --quiet; then
    print_status "MongoDB is running and accepting connections"
else
    print_error "MongoDB is not responding to connections"
    exit 1
fi

# Step 7: Display status
print_status "MongoDB system setup completed successfully!"

echo ""
echo "System Status:"
echo "============="
echo "MongoDB Version: $(mongod --version | head -1)"
echo "Service Status: $(sudo systemctl is-active mongod)"
echo "Data Directory: /mnt/data/mongodb/data"
echo "Log Directory: /mnt/data/mongodb/logs"
echo "Storage Directory: /mnt/data/arxiv_papers"
echo ""

# Check disk space
echo "Disk Usage:"
echo "==========="
df -h /mnt/data

echo ""
echo "Next Steps:"
echo "==========="
echo "1. Run the database initialization script:"
echo "   cd /mnt/projects/workspace/rxiv_paper_scraper"
echo "   python scripts/init_mongodb.py"
echo ""
echo "2. Set up authentication (recommended for production):"
echo "   export MONGODB_AUTH_ENABLED=true"
echo "   export MONGODB_ADMIN_PASSWORD='your_secure_password'"
echo "   export MONGODB_APP_PASSWORD='your_app_password'"
echo ""
echo "3. Start the arXiv scraper:"
echo "   python main.py"
echo ""
echo "4. Monitor MongoDB:"
echo "   sudo systemctl status mongod"
echo "   mongosh --eval 'db.stats()'"
echo ""

print_status "Setup complete! MongoDB is ready for the arXiv scraper project."