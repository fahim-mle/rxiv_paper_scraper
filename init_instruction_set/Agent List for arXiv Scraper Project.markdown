# Agent List for arXiv Scraper Project

## Main Agent (Orchestrator)
- **Specialty**: Project planning, task delegation, resource management.
- **Tasks**:
  - Interpret user prompts and break them into subtasks.
  - Assign tasks to sub-agents based on expertise.
  - Monitor progress, handle inter-agent communication, and resolve conflicts.
  - Ensure compliance with arXiv rate limits and project goals (e.g., NLP compatibility).
  - Example: Assign MongoDB setup to Database Agent, code optimization to Code Optimization Agent.

## Database Agent
- **Specialty**: MongoDB setup, configuration, and integration; basic Linux (Ubuntu) skills.
- **Tasks**:
  - Install MongoDB on Ubuntu: `sudo apt install mongodb`, configure server.
  - Create database (`arxiv_papers`) and collections (`papers`, `articles`).
  - Write Python code using `pymongo` to connect scraper to MongoDB.
  - Design flexible schemas for arXiv papers and other sources (e.g., books).
  - Manage backups to 300GB storage.
  - Example: Handle Step 3 (Design Database Schema), Step 5 (Store metadata in MongoDB).

## Crawler Agent
- **Specialty**: Web crawling, API interaction, async programming.
- **Tasks**:
  - Build crawler using arXiv API with `aiohttp` for async queries.
  - Parse pagination for arXiv categories (e.g., cs.AI) and other sources (e.g., Project Gutenberg).
  - Extract paper/article URLs and pass to Scraper Agent.
  - Implement rate limiting (`asyncio.sleep(3)` for arXiv).
  - Example: Handle Step 4 (Build Crawler).

## Scraper Agent
- **Specialty**: Data extraction, HTML parsing, metadata processing.
- **Tasks**:
  - Parse metadata (title, authors, abstract, PDF URL) from API or HTML using `BeautifulSoup`.
  - Extract metadata for non-arXiv sources (e.g., book titles, DOIs).
  - Pass data to Database Agent for storage.
  - Handle missing fields or broken links.
  - Example: Handle Step 5 (Build Scraper).

## Downloader Agent
- **Specialty**: Async file downloads, file system management.
- **Tasks**:
  - Download PDFs using `aiohttp` to `./papers/<category>/<paper_id>.pdf`.
  - Manage 300GB storage, organize files by source/category.
  - Implement retry logic for failed downloads.
  - Log download status.
  - Example: Handle Step 6 (Implement PDF Downloader).

## Code Optimization Agent
- **Specialty**: Python optimization, parallel processing, performance tuning.
- **Tasks**:
  - Optimize crawler/scraper code with `asyncio` and `concurrent.futures`.
  - Split tasks for MCP servers (e.g., 4-core CPU).
  - Cache API results to reduce redundant queries.
  - Profile and improve code performance (e.g., reduce I/O bottlenecks).
  - Example: Handle Step 7 (Optimize with Parallel Processing).

## Multi-Source Agent
- **Specialty**: Adapting scraper for diverse data sources, schema flexibility.
- **Tasks**:
  - Extend scraper for free books (e.g., Project Gutenberg) and articles (e.g., open-access journals).
  - Adapt MongoDB schema for varied metadata (e.g., ISBN, DOI).
  - Test compatibility with non-arXiv sources.
  - Example: Handle Step 8 (Add Multi-Source Support).

## Testing Agent
- **Specialty**: Testing, validation, error handling.
- **Tasks**:
  - Test scraper on small datasets (100 papers, 10 books/articles).
  - Verify MongoDB data integrity and PDF downloads.
  - Check server performance (CPU, memory, disk).
  - Log and report errors for debugging.
  - Example: Handle Step 9 (Test and Validate).

## Deployment Agent
- **Specialty**: Deployment, scheduling, containerization.
- **Tasks**:
  - Create Docker container for scraper portability.
  - Set up `cron` for daily runs (`0 2 * * * python scraper.py`).
  - Configure logging for errors and progress.
  - Manage MongoDB backups to 300GB storage.
  - Example: Handle Step 10 (Deploy and Schedule).

## NLP Agent
- **Specialty**: NLP/ML data preparation, integration with ML libraries.
- **Tasks**:
  - Export MongoDB data to JSON for NLP/ML tasks.
  - Ensure metadata compatibility with `nltk`, `transformers`.
  - Suggest preprocessing steps (e.g., tokenization, keyword extraction).
  - Plan future ML tasks (e.g., topic modeling, text classification).
  - Example: Handle Step 11 (Prepare for NLP/ML Use).