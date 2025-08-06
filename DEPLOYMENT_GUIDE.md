# MongoDB Deployment Guide for arXiv Scraper Project

This guide provides complete instructions for deploying MongoDB for the arXiv Scraper Project, with options for both development and production environments.

## Quick Start (No Sudo Required)

If you have write access to `/mnt/data`, you can set up MongoDB without root privileges:

```bash
cd /mnt/projects/workspace/rxiv_paper_scraper
chmod +x scripts/setup_mongodb_user.sh scripts/start_mongodb.sh scripts/stop_mongodb.sh scripts/status_mongodb.sh
./scripts/setup_mongodb_user.sh
```

This will create a working MongoDB setup in user space.

## Setup Options

### Option 1: User Mode (Recommended for Development)
- **Pros**: No root access required, easy to debug, full user control
- **Cons**: Manual startup/shutdown, not managed by systemd
- **Use case**: Development, testing, personal deployments

### Option 2: System Service Mode (For Production)
- **Pros**: Managed by systemd, automatic startup, better security
- **Cons**: Requires root access for initial setup
- **Use case**: Production servers, shared environments

## Prerequisites

1. **MongoDB Installation**: MongoDB must be installed on your system
   - Current setup tested with MongoDB 8.0.12
   - MongoDB Shell (mongosh) 2.5.6 or later

2. **Python Dependencies**:
   ```bash
   pip install pymongo>=4.0.0
   ```

3. **Disk Space**: 
   - At least 300GB available in `/mnt/data`
   - Current allocation: 458GB with 433GB available

## User Mode Setup (No Root Required)

### Step 1: Run User Setup Script

```bash
cd /mnt/projects/workspace/rxiv_paper_scraper
./scripts/setup_mongodb_user.sh
```

This script will:
- Create MongoDB directories in `/mnt/data/mongodb_user/`
- Create arXiv papers storage directories
- Generate optimized MongoDB configuration
- Start MongoDB and test the connection

### Step 2: Verify Installation

```bash
./scripts/status_mongodb.sh
```

Expected output:
```
MongoDB Status Check - arXiv Scraper Project
==============================================
Status: RUNNING (PID: xxxxx)

Connection Test:
Connection: OK

Database Statistics:
Collections: 0
Data Size: 0.00 MB
Storage Size: 0.00 MB
Indexes: 0

Disk Usage:
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p2  458G  1.9G  433G   1% /mnt/data
```

### Step 3: Test Basic Operations

```bash
mongosh --eval "
db.test.insertOne({name: 'deployment_test', timestamp: new Date()});
print('Test document inserted');
const doc = db.test.findOne();
print('Retrieved:', JSON.stringify(doc));
db.test.drop();
print('Test collection cleaned up');
"
```

## System Service Setup (Requires Root)

### Step 1: Run Root Setup First

```bash
sudo scripts/setup_mongodb_root.sh
```

This will:
- Create system directories with proper ownership
- Install MongoDB if not present
- Create mongodb system user
- Set up systemd service configuration

### Step 2: Choose Service Mode

**Option A: Enable System Service**
```bash
sudo systemctl enable mongod
sudo systemctl start mongod
sudo systemctl status mongod
```

**Option B: Continue with User Mode**
```bash
su - your_username -c 'cd /path/to/project && ./scripts/setup_mongodb_user.sh'
```

## MongoDB Management Commands

### Start MongoDB
```bash
./scripts/start_mongodb.sh
```

### Stop MongoDB
```bash
./scripts/stop_mongodb.sh
```

### Check Status
```bash
./scripts/status_mongodb.sh
```

### Connect to MongoDB
```bash
mongosh
# or with specific database
mongosh arxiv_scraper
```

## Configuration Files

### User Mode Configuration
- **Location**: `/mnt/projects/workspace/rxiv_paper_scraper/mongodb_user.conf`
- **Data Directory**: `/mnt/data/mongodb_user/data`
- **Log File**: `/mnt/data/mongodb_user/logs/mongod.log`
- **PID File**: `/mnt/data/mongodb_user/mongod.pid`

### System Service Configuration
- **Location**: `/etc/mongod.conf`
- **Data Directory**: `/mnt/data/mongodb/data`
- **Log File**: `/mnt/data/mongodb/logs/mongod.log`
- **Systemd Override**: `/etc/systemd/system/mongod.service.d/override.conf`

## Storage Layout

```
/mnt/data/
├── mongodb_user/          # User mode MongoDB
│   ├── data/             # Database files
│   └── logs/             # Log files
├── mongodb/              # System mode MongoDB (if using root setup)
│   ├── data/             # Database files  
│   └── logs/             # Log files
└── arxiv_papers/         # Paper storage
    ├── papers/           # arXiv papers
    ├── books/            # Project Gutenberg books
    ├── articles/         # Journal articles
    └── temp/             # Temporary downloads
```

## Database Initialization

After MongoDB is running, initialize the database:

```bash
cd /mnt/projects/workspace/rxiv_paper_scraper
python scripts/init_mongodb.py
```

This will create:
- Required collections (papers, books, articles, metadata)
- Optimal indexes for the scraper system
- Database users (if authentication is enabled)

## Health Monitoring

Run health checks to monitor database status:

```bash
# Full health check
python scripts/db_health_check.py

# JSON output
python scripts/db_health_check.py --json

# Specific checks
python scripts/db_health_check.py --check connection
python scripts/db_health_check.py --check storage
```

## Authentication Setup (Optional)

For production environments, enable authentication:

```bash
export MONGODB_AUTH_ENABLED=true
export MONGODB_ADMIN_PASSWORD='your_secure_admin_password'
export MONGODB_APP_PASSWORD='your_secure_app_password'

# Re-run initialization
python scripts/init_mongodb.py
```

## Troubleshooting

### MongoDB Won't Start

1. **Check if port 27017 is in use**:
   ```bash
   lsof -i :27017
   ```

2. **Check log files**:
   ```bash
   tail -f /mnt/data/mongodb_user/logs/mongod.log
   ```

3. **Verify disk space**:
   ```bash
   df -h /mnt/data
   ```

4. **Check permissions**:
   ```bash
   ls -la /mnt/data/mongodb_user/
   ```

### Connection Issues

1. **Test basic connectivity**:
   ```bash
   mongosh --eval "db.adminCommand('ping')"
   ```

2. **Check if MongoDB is listening**:
   ```bash
   netstat -tlnp | grep 27017
   ```

3. **Verify configuration**:
   ```bash
   mongod --config mongodb_user.conf --configExpand rest
   ```

### Performance Issues

1. **Check resource usage**:
   ```bash
   ./scripts/status_mongodb.sh
   ```

2. **Monitor queries**:
   ```bash
   mongosh --eval "db.setProfilingLevel(2); db.system.profile.find().limit(5).sort({ts:-1}).pretty()"
   ```

3. **Check index usage**:
   ```bash
   python scripts/db_health_check.py --check indexes
   ```

## Backup and Recovery

### Manual Backup
```bash
mongodump --out /mnt/data/backups/$(date +%Y%m%d_%H%M%S)
```

### Automated Backup (Add to crontab)
```bash
# Daily backup at 2 AM
0 2 * * * mongodump --out /mnt/data/backups/$(date +\%Y\%m\%d_\%H\%M\%S)
```

### Restore from Backup
```bash
mongorestore /mnt/data/backups/backup_directory/
```

## Production Deployment Checklist

- [ ] MongoDB installed and version verified
- [ ] Disk space allocated (300GB+)
- [ ] Authentication enabled with strong passwords
- [ ] Log rotation configured
- [ ] Backup strategy implemented
- [ ] Monitoring scripts scheduled
- [ ] Network security configured (firewall rules)
- [ ] Resource limits set (ulimit, systemd)
- [ ] SSL/TLS configured (if external access needed)
- [ ] Regular health checks scheduled

## Environment Variables

```bash
# Database configuration
export MONGODB_HOST="localhost"
export MONGODB_PORT="27017"
export MONGODB_DATABASE="arxiv_scraper"

# Authentication (optional)
export MONGODB_AUTH_ENABLED="true"
export MONGODB_ADMIN_PASSWORD="your_admin_password"
export MONGODB_APP_PASSWORD="your_app_password"

# Storage configuration
export STORAGE_BASE_PATH="/mnt/data/arxiv_papers"
export STORAGE_MAX_GB="300"
```

## Next Steps

1. **Initialize Database**: Run `python scripts/init_mongodb.py`
2. **Test Health**: Run `python scripts/db_health_check.py`
3. **Start Scraper**: Run `python main.py`
4. **Monitor**: Schedule regular health checks and backups

## Support

For issues or questions:
1. Check log files in `/mnt/data/mongodb_user/logs/`
2. Run health check diagnostics
3. Review MongoDB documentation for version-specific features
4. Test with minimal configuration if problems persist

---

**Note**: This deployment has been tested with MongoDB 8.0.12 on Ubuntu Linux with 433GB available storage space.