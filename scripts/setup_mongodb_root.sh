#!/bin/bash

# MongoDB Root Setup Script for arXiv Scraper Project
# This script contains ONLY commands that require root privileges

set -e  # Exit on any error

echo "MongoDB Root Setup for arXiv Scraper Project"
echo "============================================="
echo "WARNING: This script requires root privileges"
echo ""

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root"
    print_action "Run with: sudo $0"
    exit 1
fi

# Get the user who invoked sudo
if [ -n "$SUDO_USER" ]; then
    TARGET_USER="$SUDO_USER"
else
    print_warning "SUDO_USER not set, using 'fahim' as default"
    TARGET_USER="fahim"
fi

print_status "Setting up MongoDB system components for user: $TARGET_USER"

# Step 1: Create /mnt/data directory and set ownership
print_status "Creating /mnt/data directory structure..."

mkdir -p /mnt/data/mongodb/{data,logs}
mkdir -p /mnt/data/arxiv_papers/{papers,books,articles,temp}

# Set ownership to the target user
chown -R $TARGET_USER:$TARGET_USER /mnt/data
chmod -R 755 /mnt/data

print_status "Directory structure created and ownership set to $TARGET_USER"

# Step 2: Install MongoDB if not present
print_status "Checking MongoDB installation..."

if ! command -v mongod >/dev/null 2>&1; then
    print_status "Installing MongoDB..."
    
    # Add MongoDB repository (Ubuntu/Debian)
    if command -v apt-get >/dev/null 2>&1; then
        # Import MongoDB public GPG key
        wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
        
        # Add MongoDB repository
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
        
        # Update package database
        apt-get update
        
        # Install MongoDB
        apt-get install -y mongodb-org
        
        print_status "MongoDB installed successfully"
    else
        print_error "Unsupported package manager. Please install MongoDB manually."
        print_action "Visit: https://docs.mongodb.com/manual/installation/"
        exit 1
    fi
else
    MONGOD_VERSION=$(mongod --version | head -1)
    print_status "MongoDB already installed: $MONGOD_VERSION"
fi

# Step 3: Create mongodb user if it doesn't exist
if ! id "mongodb" &>/dev/null; then
    print_status "Creating mongodb system user..."
    useradd -r -s /bin/false mongodb
    print_status "mongodb user created"
else
    print_status "mongodb user already exists"
fi

# Step 4: Install system MongoDB configuration (optional - for systemd service)
PROJECT_ROOT="/mnt/projects/workspace/rxiv_paper_scraper"
if [ -f "$PROJECT_ROOT/mongodb.conf" ]; then
    print_status "Installing system MongoDB configuration..."
    cp "$PROJECT_ROOT/mongodb.conf" /etc/mongod.conf
    chown root:root /etc/mongod.conf
    chmod 644 /etc/mongod.conf
    print_status "System configuration installed"
fi

# Step 5: Create systemd service override (optional - for system service)
print_status "Creating systemd service override..."

mkdir -p /etc/systemd/system/mongod.service.d
cat > /etc/systemd/system/mongod.service.d/override.conf << EOF
[Service]
# Override for custom data path and configuration
ExecStart=
ExecStart=/usr/bin/mongod --config /etc/mongod.conf

# Security enhancements
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/mnt/data/mongodb

# User and group
User=mongodb
Group=mongodb
EOF

# Set ownership of MongoDB data directories to mongodb user for system service
chown -R mongodb:mongodb /mnt/data/mongodb
chmod -R 755 /mnt/data/mongodb

# Step 6: Reload systemd
print_status "Reloading systemd..."
systemctl daemon-reload

print_status "Root setup completed successfully!"

echo ""
echo "What was configured:"
echo "==================="
echo "✓ Created /mnt/data directory structure"
echo "✓ Set ownership to user: $TARGET_USER"
echo "✓ Installed MongoDB (if not present)"
echo "✓ Created mongodb system user"
echo "✓ Installed system MongoDB configuration"
echo "✓ Created systemd service override"
echo ""

echo "Choose your MongoDB deployment mode:"
echo "===================================="
echo ""
echo "Option 1: User Mode (Recommended for development)"
echo "  • Run as regular user ($TARGET_USER)"
echo "  • No systemd service"
echo "  • Easy to manage and debug"
echo "  • Run: su - $TARGET_USER -c 'cd $PROJECT_ROOT && ./scripts/setup_mongodb_user.sh'"
echo ""
echo "Option 2: System Service Mode (For production)"
echo "  • Run as mongodb system user"
echo "  • Managed by systemd"
echo "  • Automatic startup on boot"
echo "  • Run: systemctl enable mongod && systemctl start mongod"
echo ""

print_action "Recommended: Switch to user $TARGET_USER and run the user setup script"
echo "su - $TARGET_USER -c 'cd $PROJECT_ROOT && bash scripts/setup_mongodb_user.sh'"