# Quick Start Guide

**Get up and running with the arXiv Paper Scraper in 5 minutes!**

This guide assumes you're new to the project and want to start scraping papers as quickly as possible.

## ⚡ Super Quick Start (3 Steps)

### Step 1: Setup
```bash
# Clone and enter directory
git clone <repository-url>
cd arxiv_scraper

# Create Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup Database
```bash
# Quick MongoDB setup (choose one)

# Option A: Easy automated setup
./scripts/setup_mongodb_user.sh

# Option B: If you already have MongoDB running
cp .env.example .env
# Edit .env with your MongoDB settings
```

### Step 3: Start Scraping!
```bash
# Download your first 10 AI papers
python main.py --max-papers 10 --download-pdfs

# ✅ That's it! Your papers are now in the 'papers/' folder
```

## 🔍 What Just Happened?

The scraper just:
1. **Connected** to arXiv API
2. **Found** 10 recent AI/ML papers
3. **Downloaded** the PDFs to `papers/arxiv/`
4. **Stored** metadata in your MongoDB database

## 📁 Where Are My Files?

```
your-project/
├── papers/
│   └── arxiv/
│       └── 2508/           # ← Your PDFs are here!
│           ├── 2508.04663v1.pdf
│           ├── 2508.04664v1.pdf
│           └── ...
└── .env                    # ← Your config
```

## ✅ Quick Status Check

### Is everything working?
```bash
# Check if papers were downloaded
ls -la papers/arxiv/

# Check database connection
python scripts/db_health_check.py

# Check how many papers you have
python check_database.py
```

### Expected output:
```
✅ MongoDB connection: OK
✅ Papers collection: 10 documents
✅ Storage used: 15.2MB / 300GB
✅ PDF files: 10 downloaded
```

## 🎯 Common First Tasks

### Download specific research areas:
```bash
# Computer Vision papers
python main.py --categories "cs.CV" --max-papers 20 --download-pdfs

# Natural Language Processing
python main.py --categories "cs.CL" --max-papers 15 --download-pdfs

# Machine Learning theory
python main.py --categories "cs.LG,stat.ML" --max-papers 25 --download-pdfs
```

### Search for specific topics:
```bash
# Papers about transformers
python main.py --keywords "transformer,attention" --max-papers 30 --download-pdfs

# Papers about computer vision
python main.py --keywords "computer vision,object detection" --max-papers 20 --download-pdfs
```

### Download recent papers:
```bash
# Papers from last 7 days
python main.py --days-back 7 --max-papers 50 --download-pdfs

# Papers from last 2 days (very recent)
python main.py --days-back 2 --max-papers 20 --download-pdfs
```

## 🆘 Something Wrong?

### MongoDB won't connect?
```bash
# Check if MongoDB is running
./scripts/status_mongodb.sh

# If not running, start it
./scripts/start_mongodb.sh

# Still problems? Check the logs
tail -f /mnt/data/mongodb/logs/mongodb.log
```

### No papers found?
```bash
# Try with debug logging to see what's happening
python main.py --max-papers 5 --log-level DEBUG

# Check if arXiv API is accessible
curl "http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1"
```

### Storage issues?
```bash
# Check available space
df -h .

# Check current usage
du -sh papers/
```

## 🚀 Ready for More?

Once you have the basics working:

1. **Read [WORKFLOWS.md](WORKFLOWS.md)** for common research scenarios
2. **Check [EXAMPLES.md](EXAMPLES.md)** for advanced usage patterns  
3. **See [FAQ.md](FAQ.md)** for troubleshooting
4. **Review the full [README.md](README.md)** for complete documentation

## 📝 Configuration Quick Reference

**Essential settings in `.env`:**
```bash
# Database (most important)
MONGODB_HOST=localhost
MONGODB_USERNAME=arxiv_app
MONGODB_PASSWORD=your_password

# Storage location
STORAGE_BASE_PATH=/mnt/data/arxiv_papers
MAX_STORAGE_GB=300

# Rate limiting (respect arXiv!)
ARXIV_RATE_LIMIT_SECONDS=3.0  # Don't go below 3.0
```

## 🎉 Success Indicators

You know everything is working when:

- ✅ `python main.py --max-papers 5` completes without errors
- ✅ PDF files appear in `papers/arxiv/` directory  
- ✅ `python check_database.py` shows papers in database
- ✅ Storage stats show reasonable usage (< 90%)
- ✅ No error messages in console output

**Happy scraping! 🔬📚**

---
*Need help? Check [FAQ.md](FAQ.md) or [WORKFLOWS.md](WORKFLOWS.md) for more guidance.*