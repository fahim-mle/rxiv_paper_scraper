# MCP Servers Deployment Guide for arXiv Scraper

This guide provides comprehensive instructions for deploying and managing MCP (Model Context Protocol) servers for the arXiv Scraper Project in production environments.

## 🚀 Quick Start

### Prerequisites

- **Operating System**: Ubuntu 20.04+ or similar Linux distribution
- **Python**: 3.12+ with pip and venv
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 300GB available space
- **Network**: Stable internet connection

### 1. Initial Setup

```bash
# Clone and setup the project
git clone <repository-url>
cd rxiv_paper_scraper

# Run the automated setup script
chmod +x setup_mcp_servers.sh
./setup_mcp_servers.sh

# Install project dependencies
pip install -r requirements.txt
```

### 2. Start MCP Servers

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start all available MCP servers
./scripts/start_mcp_servers.sh

# Check server status
./scripts/status_mcp_servers.sh

# Test connections
python test_mcp_connections.py
```

### 3. Stop MCP Servers

```bash
# Stop all servers gracefully
./scripts/stop_mcp_servers.sh
```

## 📋 Available MCP Servers

| Server | Status | Purpose | Port | Dependencies |
|--------|--------|---------|------|-------------|
| **arXiv MCP** | ✅ Ready | Paper search, download, analysis | 3001 | Python, arxiv library |
| **Fetch MCP** | ✅ Ready | Web content fetching | 3004 | Python, httpx |
| **Playwright MCP** | ⏳ Manual Setup | Browser automation | 3002 | Node.js, Playwright |
| **Unstructured MCP** | ⏳ Manual Setup | Document processing | 3003 | Python, ML libraries |
| **Tinybird MCP** | ⏳ Manual Setup | Analytics database | 3005 | Database connection |
| **PiloTY MCP** | ⏳ Manual Setup | Terminal management | 3006 | SSH configuration |

## 🐳 Docker Deployment (Recommended for Production)

### Prerequisites for Docker

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ available RAM

### Deploy with Docker Compose

```bash
# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f mcp-servers

# Stop all services
docker-compose down
```

### Docker Services

The Docker deployment includes:

- **MongoDB**: Document database for metadata storage
- **arXiv Scraper**: Main application with web API
- **MCP Servers**: All configured MCP servers
- **Redis**: Caching and job queues
- **Nginx**: Reverse proxy and load balancer

## 🔧 Manual Configuration

### arXiv MCP Server Configuration

```bash
# Install the server
cd external_mcp_servers/arxiv-mcp-server
pip install -e .

# Start manually
python -m arxiv_mcp_server --storage-path /path/to/papers/

# Configuration via environment variables
export ARXIV_STORAGE_PATH="/app/papers"
export ARXIV_MAX_RESULTS=50
export ARXIV_BATCH_SIZE=20
```

### Fetch MCP Server Configuration

```bash
# Install the server
cd external_mcp_servers/servers/src/fetch
pip install -e .

# Start manually
mcp-server-fetch --user-agent "arXiv-Scraper/1.0"

# Configuration options
mcp-server-fetch --help
```

### Setting Up Additional Servers

#### Playwright MCP Server (Node.js)
```bash
# Install Node.js (if not available)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install and setup
cd external_mcp_servers/servers/src/playwright
npm install
node index.js --port 3002
```

#### Unstructured MCP Server (Heavy ML Dependencies)
```bash
# Warning: This installation is large (2GB+) and slow
pip install "unstructured[all-docs]"

# Start as needed - resource intensive
python -m unstructured_server --port 3003
```

## 📊 Monitoring and Logging

### Log Files

All server logs are stored in:
- `logs/mcp_servers/*.log` - Individual server logs
- `logs/pids/*.pid` - Process ID files

### Monitoring Commands

```bash
# Real-time server status
watch -n 5 ./scripts/status_mcp_servers.sh

# View logs
tail -f logs/mcp_servers/arxiv.log
tail -f logs/mcp_servers/fetch.log

# System resource usage
htop
df -h  # Check disk usage
```

### Health Checks

```bash
# Test all MCP connections
python test_mcp_connections.py

# Individual server health
curl http://localhost:3001/health  # arXiv (if available)
curl http://localhost:3004/health  # Fetch (if available)
```

## ⚙️ Production Configuration

### Environment Variables

Create a `.env` file with:

```env
# Database Configuration
MONGO_URI=mongodb://localhost:27017/arxiv_scraper
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=secure_password_here

# Storage Configuration
STORAGE_LIMIT_GB=300
ARXIV_STORAGE_PATH=/app/papers

# MCP Server Configuration
LOG_LEVEL=INFO
MCP_SERVER_TIMEOUT=60

# Security
API_KEY=your_api_key_here
ALLOWED_ORIGINS=https://yourdomain.com
```

### System Service Setup (systemd)

Create service files for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/arxiv-mcp-servers.service
```

```ini
[Unit]
Description=arXiv Scraper MCP Servers
After=network.target

[Service]
Type=forking
User=arxiv
Group=arxiv
WorkingDirectory=/opt/arxiv_scraper
ExecStart=/opt/arxiv_scraper/scripts/start_mcp_servers.sh
ExecStop=/opt/arxiv_scraper/scripts/stop_mcp_servers.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl enable arxiv-mcp-servers
sudo systemctl start arxiv-mcp-servers
sudo systemctl status arxiv-mcp-servers
```

### Nginx Configuration

For production deployment with SSL:

```nginx
# /etc/nginx/sites-available/arxiv-scraper
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Main application
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # MCP servers (if needed for external access)
    location /mcp/arxiv/ {
        proxy_pass http://localhost:3001/;
    }
    
    location /mcp/fetch/ {
        proxy_pass http://localhost:3004/;
    }
}
```

## 🔒 Security Considerations

### Network Security
- Use firewall rules to restrict MCP server access
- Consider VPN for server-to-server communication
- Implement rate limiting for API endpoints

### Access Control
- Use strong passwords for database connections
- Implement API key authentication
- Regular security updates

### Data Protection
- Encrypt sensitive data at rest
- Use HTTPS for all external communications
- Regular backups of critical data

## 🚨 Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check if port is already in use
netstat -tuln | grep :3001

# Check server logs
tail -f logs/mcp_servers/arxiv.log

# Verify Python path and dependencies
python -m arxiv_mcp_server --help
```

#### Connection Failures
```bash
# Test network connectivity
telnet localhost 3001

# Check firewall settings
sudo ufw status

# Verify server is listening
ss -tuln | grep :3001
```

#### High Memory Usage
```bash
# Check resource usage
ps aux | grep mcp
free -h

# Restart servers to clear memory leaks
./scripts/stop_mcp_servers.sh
./scripts/start_mcp_servers.sh
```

### Performance Tuning

#### For High Load
- Increase server timeout values
- Add load balancing with multiple server instances
- Use Redis for caching frequent requests
- Implement request queuing

#### For Limited Resources
- Disable non-essential MCP servers
- Reduce batch sizes and concurrent connections
- Use swap if physical memory is limited

## 📞 Support and Maintenance

### Regular Maintenance Tasks

1. **Daily**: Check server status and logs
2. **Weekly**: Review disk usage and clean old logs
3. **Monthly**: Update dependencies and security patches
4. **Quarterly**: Full system backup and disaster recovery test

### Getting Help

- Check logs first: `logs/mcp_servers/`
- Run diagnostics: `python test_mcp_connections.py`
- Review this documentation
- Contact system administrator

## 📝 Configuration Files Summary

| File | Purpose | Location |
|------|---------|----------|
| `setup_mcp_servers.sh` | Initial setup script | Project root |
| `scripts/start_mcp_servers.sh` | Start all servers | scripts/ |
| `scripts/stop_mcp_servers.sh` | Stop all servers | scripts/ |
| `scripts/status_mcp_servers.sh` | Check server status | scripts/ |
| `docker-compose.yml` | Docker deployment | Project root |
| `Dockerfile.mcp` | MCP servers container | Project root |
| `.env` | Environment configuration | Project root |

## 🎯 Next Steps

After successful deployment:

1. **Configure monitoring** - Set up alerting for server failures
2. **Implement backups** - Regular data backup strategy
3. **Scale as needed** - Add more server instances for load
4. **Optimize performance** - Fine-tune based on usage patterns
5. **Security hardening** - Implement additional security measures

For questions or issues, refer to the troubleshooting section or check the project documentation.

---

**Version**: 1.0  
**Last Updated**: 2025-08-07  
**Deployment Agent**: arXiv Scraper Project