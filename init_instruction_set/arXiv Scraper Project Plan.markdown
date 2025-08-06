# arXiv Scraper Project Plan

## Step 1: Project Setup

- Install Python 3.10+.
- Set up virtual environment: `python -m venv venv`.
- Install libraries: `pip install pymongo aiohttp arxiv beautifulsoup4`.
- Install MongoDB server locally or use cloud (e.g., MongoDB Atlas).
- Create project folder: `arxiv_scraper`.
- Initialize git: `git init`.

## Step 2: Clone and Analyze GitHub Repos

- Clone repos: `git clone https://github.com/Mahdisadjadi/arxivscraper.git` (and others like `jannisborn/paperscraper`).
- Store in `assets/repos/`.
- Review code for API queries, PDF downloads, and metadata parsing.
- Note key functions for reuse (e.g., API filters, download logic).

## Step 3: Design Database Schema

- Create MongoDB database: `arxiv_papers`.
- Define collection: `papers` with fields (`paper_id`, `title`, `authors`, `abstract`, `pdf_url`, `date`).
- Add collection for articles/books (flexible schema for future NLP use).
- Test connection: `client = pymongo.MongoClient('mongodb://localhost:27017')`.

## Step 4: Build Crawler

- Use arXiv API for metadata (e.g., `cat:cs.AI`, date range: 2023-01-01 to 2025-08-01).
- Implement `aiohttp` for async API queries.
- Crawl web pages with `BeautifulSoup` for non-API data (e.g., free books/articles).
- Follow pagination to collect all paper/article URLs.

## Step 5: Build Scraper

- Parse metadata (title, authors, abstract, etc.) from API or HTML.
- Extract PDF URLs for arXiv papers and other sources.
- Store metadata in MongoDB: `db.papers.insert_one({...})`.
- Handle errors (e.g., missing fields, broken links).

## Step 6: Implement PDF Downloader

- Download PDFs using `aiohttp` for async requests.
- Save to `./papers/<category>/<paper_id>.pdf` (300GB storage).
- Add rate limiting: `asyncio.sleep(3)` for arXiv compliance.
- Log download status to file.

## Step 7: Optimize with Parallel Processing

- Use `asyncio` for concurrent API queries and downloads.
- Split tasks across MCP servers (e.g., 4-core CPU).
- Cache API results to avoid redundant queries.
- Test on 50 papers to verify speed.

## Step 8: Add Multi-Source Support

- Extend scraper for free books/articles (e.g., Project Gutenberg, open-access journals).
- Adapt schema for diverse metadata (e.g., book ISBN, article DOI).
- Use flexible MongoDB fields for varied data types.
- Test with 10 non-arXiv items.

## Step 9: Test and Validate

- Run scraper on small dataset (100 papers, 10 books/articles).
- Check MongoDB for complete metadata.
- Verify PDF integrity and storage.
- Monitor server performance (CPU, memory, disk).

## Step 10: Deploy and Schedule

- Create Docker container for portability.
- Schedule daily runs with `cron` (e.g., `0 2 * * * python scraper.py`).
- Set up logging for errors and progress.
- Backup MongoDB to 300GB storage weekly.

## Step 11: Prepare for NLP/ML Use

- Export MongoDB data to JSON for NLP preprocessing.
- Test data compatibility with NLP libraries (e.g., `nltk`, `transformers`).
- Document metadata fields for ML tasks (e.g., text classification, topic modeling).
- Plan future extensions (e.g., keyword-based filtering, author networks).
