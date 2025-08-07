# Frequently Asked Questions (FAQ)

**Quick answers to common questions and issues**

## 🚀 Getting Started

### Q: I'm completely new to this. Where do I start?
**A:** Start with [QUICK_START.md](QUICK_START.md)! It gets you running in 5 minutes. Once that works, explore [WORKFLOWS.md](WORKFLOWS.md) for your specific use case.

### Q: Do I need to be a programmer to use this?
**A:** No! The basic usage is just copy-pasting commands. However, for advanced analysis you'll benefit from some Python knowledge.

### Q: What operating system does this work on?
**A:** 
- ✅ **Linux**: Fully supported and recommended
- ✅ **macOS**: Supported with Homebrew
- ⚠️ **Windows**: Works with WSL (Windows Subsystem for Linux)

---

## ⚙️ Installation & Setup

### Q: MongoDB setup failed. What should I do?
**A:** Try these steps in order:

```bash
# 1. Check if MongoDB is already running
ps aux | grep mongod

# 2. If running, stop it first
sudo service mongod stop
# or
./scripts/stop_mongodb.sh

# 3. Clean start with our setup
./scripts/setup_mongodb_user.sh

# 4. Check if it worked
./scripts/status_mongodb.sh
```

If still failing:
```bash
# Check logs for specific error
tail -f /mnt/data/mongodb/logs/mongodb.log
```

### Q: I get "Permission denied" errors during setup
**A:** 
```bash
# Make scripts executable
chmod +x scripts/*.sh

# If MongoDB data directory issues:
sudo mkdir -p /mnt/data/mongodb/{data,logs}
sudo chown -R $USER:$USER /mnt/data/mongodb
```

### Q: Python dependencies won't install
**A:** 
```bash
# Update pip first
python -m pip install --upgrade pip

# Install with verbose output to see what's failing
pip install -r requirements.txt -v

# If specific package fails, try installing individually
pip install pymongo
pip install aiohttp
pip install beautifulsoup4
```

---

## 🔧 Configuration

### Q: What MongoDB settings should I use?
**A:** For most users, the defaults work fine:
```bash
# In .env file:
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=arxiv_scraper
MONGODB_USERNAME=arxiv_app
MONGODB_PASSWORD=your_secure_password  # Change this!
```

### Q: How much storage space do I need?
**A:** It depends on your usage:
- **Metadata only**: ~1MB per 1,000 papers
- **With PDFs**: ~200MB per 1,000 papers (average)
- **Recommendation**: Start with 50GB, expand as needed

### Q: What's the optimal rate limiting for arXiv?
**A:** 
```bash
# Required minimum (arXiv terms of service)
--rate-limit 3.0

# Conservative (recommended for large collections)
--rate-limit 5.0

# Never go below 3.0 - you'll get blocked!
```

---

## 🏃 Running & Usage

### Q: "No papers found" - what's wrong?
**A:** Check these common issues:

1. **Too narrow search**:
   ```bash
   # Instead of very specific terms
   python main.py --keywords "very specific research term"
   
   # Try broader categories
   python main.py --categories "cs.AI,cs.LG" --max-papers 20
   ```

2. **Date range too short**:
   ```bash
   # Instead of recent only
   python main.py --days-back 7
   
   # Try longer period
   python main.py --days-back 90
   ```

3. **arXiv API issues**:
   ```bash
   # Test arXiv directly
   curl "http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1"
   ```

### Q: Downloads are very slow. How can I speed them up?
**A:** Several approaches:

```bash
# 1. Skip PDFs for faster metadata collection
python main.py --max-papers 100  # No --download-pdfs

# 2. Increase concurrent downloads (carefully!)
python main.py --download-pdfs --max-concurrent 5

# 3. Check your internet speed
speedtest-cli

# 4. Use smaller batches
python main.py --max-papers 25 --download-pdfs
```

### Q: I'm getting "Rate limit exceeded" errors
**A:** 
```bash
# 1. Increase delay between requests
python main.py --rate-limit 5.0 --pdf-rate-limit 3.0

# 2. Reduce concurrent operations
python main.py --max-concurrent 1

# 3. If persistent, wait 10 minutes then retry
```

### Q: How do I search for specific topics effectively?
**A:** Use layered search strategies:

```bash
# 1. Start broad
python main.py --categories "cs.AI" --max-papers 50

# 2. Add specific keywords
python main.py --keywords "transformer,attention" --categories "cs.CL,cs.LG" --max-papers 30

# 3. Try related terms
python main.py --keywords "neural network,deep learning,machine learning" --max-papers 40
```

---

## 💾 Data Management

### Q: How do I check what papers I've collected?
**A:** 
```bash
# Quick check
python check_database.py

# Detailed statistics
python -c "
from arxiv_scraper.database.mongodb_operations import get_operations
db_ops = get_operations()
stats = db_ops.get_collection_stats()
for collection, info in stats.items():
    print(f'{collection}: {info[\"document_count\"]} papers')
"

# Check PDF files
ls -la papers/arxiv/ | head -10
du -sh papers/
```

### Q: My database is getting too large. How do I clean it up?
**A:** 
```bash
# 1. Check current usage
python -c "
import pymongo
client = pymongo.MongoClient()
db = client.arxiv_scraper
total = db.papers.count_documents({})
print(f'Total papers: {total}')
"

# 2. Remove old papers (older than 2 years)
python -c "
import pymongo
from datetime import datetime, timedelta
client = pymongo.MongoClient()
db = client.arxiv_scraper
old_date = datetime.now() - timedelta(days=730)
result = db.papers.delete_many({'date_published': {'\\$lt': old_date.isoformat()}})
print(f'Deleted {result.deleted_count} old papers')
"

# 3. Clean up orphaned PDF files
python -c "
from arxiv_scraper.scraper.pdf_downloader import StorageManager
storage = StorageManager()
cleaned = storage.cleanup_old_files()
print(f'Cleaned {cleaned} files')
"
```

### Q: How do I backup my data?
**A:** 
```bash
# 1. Backup MongoDB
mongodump --db arxiv_scraper --out backup_$(date +%Y%m%d)

# 2. Backup PDF files
tar -czf papers_backup_$(date +%Y%m%d).tar.gz papers/

# 3. Backup configuration
cp .env .env.backup
```

### Q: Can I export my data to other formats?
**A:** Yes! See [EXAMPLES.md](EXAMPLES.md) for detailed export scripts. Quick examples:

```bash
# Export to CSV
python -c "
import pandas as pd
from arxiv_scraper.database.mongodb_operations import get_operations
db_ops = get_operations()
papers = list(db_ops.find_papers({}))
df = pd.DataFrame(papers)
df.to_csv('all_papers.csv', index=False)
print(f'Exported {len(df)} papers to CSV')
"

# Export to JSON
python -c "
import json
from arxiv_scraper.database.mongodb_operations import get_operations
db_ops = get_operations()
papers = list(db_ops.find_papers({}))
with open('all_papers.json', 'w') as f:
    json.dump(papers, f, indent=2, default=str)
print(f'Exported {len(papers)} papers to JSON')
"
```

---

## 🔍 Search & Filtering

### Q: What arXiv categories should I use for my research area?
**A:** Common categories by field:

**Artificial Intelligence**:
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.NE` - Neural and Evolutionary Computing

**Computer Vision**:
- `cs.CV` - Computer Vision and Pattern Recognition

**Natural Language Processing**:
- `cs.CL` - Computation and Language

**Robotics**:
- `cs.RO` - Robotics

**Statistics/Math**:
- `stat.ML` - Machine Learning (Statistics)
- `math.OC` - Optimization and Control

**Full list**: https://arxiv.org/category_taxonomy

### Q: How do I find papers by specific authors?
**A:** 
```bash
# Search in keywords (authors often mentioned in abstracts)
python main.py --keywords "Geoffrey Hinton,Yann LeCun" --max-papers 50

# Or search database after collection
python -c "
from arxiv_scraper.database.mongodb_operations import get_operations
db_ops = get_operations()
papers = list(db_ops.find_papers({'authors': {'\\$regex': 'Hinton', '\\$options': 'i'}}))
print(f'Found {len(papers)} papers with Hinton as author')
for paper in papers[:5]:
    print(f'- {paper[\"title\"]}')
"
```

### Q: How do I search for papers within a specific date range?
**A:** 
```bash
# Last 30 days
python main.py --days-back 30 --max-papers 100

# Custom date range (requires direct database query)
python -c "
from arxiv_scraper.database.mongodb_operations import get_operations
db_ops = get_operations()
papers = list(db_ops.get_papers_by_date_range('2024-01-01', '2024-06-30'))
print(f'Found {len(papers)} papers from first half of 2024')
"
```

---

## ⚠️ Troubleshooting

### Q: The scraper crashes with "Connection timeout"
**A:** 
```bash
# 1. Check internet connection
ping arxiv.org

# 2. Increase timeout
python -c "
from arxiv_scraper.config.settings import get_settings
settings = get_settings()
print(f'Current timeout: {settings.scraping.request_timeout_seconds}s')
"

# 3. In .env file, increase:
# REQUEST_TIMEOUT_SECONDS=60

# 4. Try with smaller batches
python main.py --max-papers 10 --log-level DEBUG
```

### Q: "Storage full" error but I have space available
**A:** 
```bash
# Check actual disk space
df -h /mnt/data

# Check scraper's storage calculation
python -c "
from arxiv_scraper.scraper.pdf_downloader import StorageManager
storage = StorageManager()
stats = storage.get_storage_stats()
print(f'Scraper thinks: {stats[\"current_usage_gb\"]:.1f}GB used')
print(f'Available: {stats[\"available_gb\"]:.1f}GB')
print(f'Limit: {stats[\"max_storage_gb\"]}GB')
"

# If calculation is wrong, clean up and restart
python -c "
from arxiv_scraper.scraper.pdf_downloader import StorageManager
storage = StorageManager()
cleaned = storage.cleanup_old_files()
print(f'Cleaned {cleaned} files')
"
```

### Q: Papers downloaded but not showing in database
**A:** 
```bash
# Check database connection
python scripts/db_health_check.py

# Check for insert errors
python main.py --max-papers 5 --log-level DEBUG --log-file debug.log
grep -i error debug.log

# Manual database check
python -c "
from arxiv_scraper.database.mongodb_operations import get_operations
db_ops = get_operations()
recent = list(db_ops.find_papers({}, limit=5))
print(f'Found {len(recent)} recent papers')
for paper in recent:
    print(f'- {paper.get(\"title\", \"No title\")}')
"
```

### Q: MCP servers not working
**A:** 
```bash
# Check MCP server status
python test_mcp_connections.py

# Start MCP servers
./scripts/start_mcp_servers.sh

# Check MCP server logs
tail -f logs/mcp_servers/arxiv.log

# Fallback: scraper works without MCP
python main.py --max-papers 10  # Should work even without MCP
```

---

## 🚀 Performance & Optimization

### Q: How can I make the scraper faster?
**A:** Several optimization strategies:

1. **Skip PDFs for metadata-only collection**:
   ```bash
   python main.py --max-papers 500  # No --download-pdfs
   ```

2. **Optimize database operations**:
   ```bash
   # Increase batch size in .env
   BATCH_SIZE=200
   ```

3. **Use appropriate hardware**:
   - SSD storage for database
   - Good internet connection
   - Sufficient RAM (4GB+ recommended)

### Q: The scraper uses too much memory
**A:** 
```bash
# 1. Reduce batch sizes
# In .env:
BATCH_SIZE=50

# 2. Use smaller paper limits
python main.py --max-papers 25 --download-pdfs

# 3. Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f}MB')
"
```

---

## 🌐 Advanced Usage

### Q: Can I scrape from sources other than arXiv?
**A:** Yes! The system supports multiple sources:

```bash
# The scraper is designed for multiple sources
# Currently implemented: arXiv
# Planned: PubMed, bioRxiv, Project Gutenberg

# Check multi-source agent status
python -c "
from arxiv_scraper.config.settings import get_settings
settings = get_settings()
print(f'Multi-source agent enabled: {settings.agents.enable_multi_source_agent}')
"
```

### Q: How do I integrate this with my research workflow?
**A:** See [WORKFLOWS.md](WORKFLOWS.md) for detailed examples. Quick integration ideas:

```bash
# Daily research alerts
./daily_research_alerts.py > daily_papers.txt

# Weekly bibliography updates
python weekly_bibliography_generator.py

# Export for citation managers
python export_to_mendeley.py
```

### Q: Can I run this in the cloud?
**A:** Yes! See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for cloud deployment options:

- AWS EC2 with MongoDB Atlas
- Google Cloud Platform
- Docker containers
- Kubernetes deployment

---

## ❓ Still Need Help?

### Getting more help:
1. **Check logs**: Always look at error logs first
   ```bash
   python main.py --log-level DEBUG --log-file debug.log
   tail -f debug.log
   ```

2. **Test with minimal examples**:
   ```bash
   python main.py --max-papers 1 --log-level DEBUG
   ```

3. **Check system health**:
   ```bash
   ./scripts/status_mongodb.sh
   python scripts/db_health_check.py
   python test_mcp_connections.py
   ```

4. **Community resources**:
   - GitHub Issues: For bugs and feature requests
   - GitHub Discussions: For questions and community help
   - Documentation: [README.md](README.md) for comprehensive guide

### Before reporting issues, please include:
- Operating system and version
- Python version (`python --version`)
- Full error message and traceback
- Steps to reproduce the issue
- Your `.env` configuration (remove passwords!)

---

## 🎉 Success Stories

### Q: How do I know if everything is working correctly?
**A:** Look for these success indicators:

✅ **Successful run output**:
```
==========================================
SCRAPER RUN SUMMARY
==========================================
Papers crawled:    50
Papers processed:  50
Papers stored:     50
PDFs downloaded:   47
Download size:     156.3MB

Database totals:
  papers: 50 papers
```

✅ **Health check passes**:
```bash
python scripts/db_health_check.py
# Should show: MongoDB connection: OK
```

✅ **Files in expected locations**:
```bash
ls papers/arxiv/
# Should show dated folders with PDF files
```

---

*Can't find your question? Check [WORKFLOWS.md](WORKFLOWS.md) for specific use cases or [EXAMPLES.md](EXAMPLES.md) for code examples.*