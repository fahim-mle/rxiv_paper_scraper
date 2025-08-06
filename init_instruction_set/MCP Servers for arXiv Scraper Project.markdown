# MCP Servers for arXiv Scraper Project

## 1. arXiv MCP Server

- **Purpose**: Fetch and process arXiv papers and LaTeX sources.
- **Agent Usage**: Crawler Agent, Scraper Agent.
- **Benefits**:
  - Queries arXiv API for metadata (e.g., `cat:cs.AI`, date range: 2023-01-01 to 2025-08-01).
  - Processes LaTeX for precise mathematical expression extraction.
  - Supports async JSON-RPC calls for high-speed data retrieval.
- **Implementation**:
  - Source: `blazickjp/arxiv-mcp-server` (GitHub).
  - Configure: Set `--storage-path` for 300GB storage.
  - Example: `await call_tool("search_papers", {"query": "machine learning", "max_results": 100})`.
- **Trustworthiness**: Community-verified, active maintenance, aligns with arXiv’s API guidelines.
- **Project Impact**: Accelerates metadata collection for Steps 4 (Build Crawler) and 5 (Build Scraper).
- **Tasks**: Step 4 (Build Crawler), Step 5 (Build Scraper).[](https://github.com/modelcontextprotocol/servers)

## 2. Playwright MCP Server

- **Purpose**: Browser automation for scraping non-API sources.
- **Agent Usage**: Crawler Agent, Multi-Source Agent.
- **Benefits**:
  - Scrapes JavaScript-heavy sites (e.g., Project Gutenberg, open-access journals).
  - Bypasses anti-bot measures using headless browsers and proxy rotation.
  - Outputs HTML for `BeautifulSoup` parsing.
- **Implementation**:
  - Source: `modelcontextprotocol/servers` (GitHub).
  - Configure: Enable proxy rotation for dynamic sites.
  - Example: Scrape book metadata from Gutenberg.
- **Trustworthiness**: Official MCP server, widely adopted, secure with Pomerium integration.
- **Project Impact**: Enables Step 8 (Add Multi-Source Support) for books and articles.
- **Tasks**: Step 4 (Build Crawler), Step 8 (Add Multi-Source Support).[](https://www.pomerium.com/blog/best-model-context-protocol-mcp-servers-in-2025)

## 3. Unstructured MCP Server

- **Purpose**: Extract structured data from PDFs and HTML.
- **Agent Usage**: Scraper Agent, NLP Agent.
- **Benefits**:
  - Converts arXiv PDFs and web content to JSON/Markdown for MongoDB.
  - Preprocesses text for NLP (e.g., tokenization, keyword extraction).
  - Scales for 300GB dataset processing.
- **Implementation**:
  - Source: `unstructured-io/unstructured`.
  - Configure: Connect to MongoDB for storing processed data.
  - Example: Extract abstract text from PDFs.
- **Trustworthiness**: Open-source, well-maintained by Unstructured.io, used in enterprise NLP.
- **Project Impact**: Enhances Step 5 (Build Scraper) and Step 11 (Prepare for NLP/ML Use).
- **Tasks**: Step 5 (Build Scraper), Step 11 (Prepare for NLP/ML Use).

## 4. Fetch MCP Server

- **Purpose**: Real-time web content fetching and formatting.
- **Agent Usage**: Crawler Agent, Multi-Source Agent.
- **Benefits**:
  - Fetches and converts web content (e.g., articles, books) to LLM-friendly formats.
  - Supports real-time scraping for dynamic sources.
  - Integrates with MongoDB for metadata storage.
- **Implementation**:
  - Source: `modelcontextprotocol/servers` (GitHub).
  - Configure: Set up for Markdown output.
  - Example: Fetch article content for NLP preprocessing.
- **Trustworthiness**: Official MCP server, high GitHub stars, secure file operations.
- **Project Impact**: Supports Step 8 (Add Multi-Source Support) for diverse sources.
- **Tasks**: Step 4 (Build Crawler), Step 8 (Add Multi-Source Support).[](https://dev.to/itshayder/top-7-free-mcp-servers-in-2025-to-supercharge-your-ai-apps-open-source-ready-to-use-5die)

## 5. Tinybird MCP Server

- **Purpose**: Serverless data processing with ClickHouse for analytics.
- **Agent Usage**: Database Agent, Testing Agent.
- **Benefits**:
  - Stores metadata in MongoDB-compatible format for 300GB dataset.
  - Enables real-time analytics (e.g., duplicate checks, query performance).
  - Scales for large-scale metadata queries.
- **Implementation**:
  - Source: `tinybirdco/mcp-server`.
  - Configure: Set up ClickHouse for MongoDB integration.
  - Example: Query paper metadata for validation.
- **Trustworthiness**: Backed by Tinybird, enterprise-grade, secure data handling.
- **Project Impact**: Improves Step 3 (Design Database Schema) and Step 9 (Test and Validate).
- **Tasks**: Step 3 (Design Database Schema), Step 9 (Test and Validate).

## 6. PiloTY MCP Server

- **Purpose**: Manage terminals and background processes on MCP servers.
- **Agent Usage**: Deployment Agent, Code Optimization Agent.
- **Benefits**:
  - Manages scraper scheduling on Ubuntu servers.
  - Supports SSH for 4-core MCP server tasks.
  - Monitors parallel processing (e.g., `asyncio` tasks).
- **Implementation**:
  - Source: `pilotymcp/piloty`.
  - Configure: Set up SSH for cron jobs.
  - Example: Schedule daily scraper runs.
- **Trustworthiness**: Community-driven, secure terminal management, audited for safety.
- **Project Impact**: Streamlines Step 7 (Optimize with Parallel Processing) and Step 10 (Deploy and Schedule).
- **Tasks**: Step 7 (Optimize with Parallel Processing), Step 10 (Deploy and Schedule).

For each MCP server, clone and install:

1. arXiv MCP Server:
   - Clone: <https://github.com/blazickjp/arxiv-mcp-server>
   - Install in: ./mcp_servers/arxiv/
   - Configure storage path: ./papers/

2. Playwright MCP Server:
   - Clone: <https://github.com/modelcontextprotocol/servers>
   - Use: src/playwright/
   - Install Node.js dependencies

3. Unstructured MCP Server:
   - Clone: <https://github.com/unstructured-io/unstructured>
   - Install Python package
   - Configure for PDF processing

4. Fetch MCP Server:
   - Use from modelcontextprotocol/servers
   - Configure for web content fetching

5. Tinybird MCP Server:
   - Clone: <https://github.com/tinybirdco/mcp-server>
   - Configure ClickHouse integration

6. PiloTY MCP Server:
   - Clone: <https://github.com/pilotymcp/piloty>
   - Configure for process management

Modify specialized agents in /mnt/projects/workspace/rxiv_paper_scraper/.claude/agents:

1. CrawlerAgent (agents/crawler.py):
   - Uses: arXiv MCP, Fetch MCP, Playwright MCP
   - Function: Fetch paper metadata from APIs and web sources
   - Methods: crawl_arxiv(), crawl_web_sources(), extract_paper_urls()

2. ScraperAgent (agents/scraper.py):
   - Uses: Unstructured MCP, arXiv MCP
   - Function: Parse metadata and extract structured data
   - Methods: parse_metadata(), extract_pdf_text(), clean_data()

3. DownloaderAgent (agents/downloader.py):
   - Uses: Fetch MCP
   - Function: Download PDFs with rate limiting
   - Methods: download_pdf(), manage_storage(), verify_integrity()

4. DatabaseAgent (agents/database.py):
   - Uses: Tinybird MCP
   - Function: Store and query MongoDB data
   - Methods: store_paper(), check_duplicates(), query_metadata()

5. NLPAgent (agents/nlp.py):
   - Uses: Unstructured MCP
   - Function: Prepare data for ML/NLP processing
   - Methods: preprocess_text(), extract_features(), export_for_ml()

6. DeploymentAgent (agents/deployment.py):
   - Uses: PiloTY MCP
   - Function: Manage processes and scheduling
   - Methods: schedule_scraper(), monitor_processes(), manage_logs()

## Notes

- **LangExtract Exclusion**: Google’s LangExtract lacks MCP integration or open-source availability, limiting its use. It could preprocess PDFs for NLP (Step 11) but requires custom setup, reducing immediate applicability.
- **Trustworthiness**: All servers are sourced from reputable GitHub repos (`modelcontextprotocol/servers`, `unstructured-io`, `tinybirdco`) with active maintenance, high stars, and secure configurations (e.g., Pomerium, SonarQube auditing). Avoid unverified servers like `code-assistant` due to prompt injection risks.[](https://arxiv.org/html/2506.13538v1)
- **Security**: Run servers in Docker containers on Ubuntu to isolate processes and protect 300GB storage. Use Pomerium for Zero Trust security.[](https://www.pomerium.com/blog/best-model-context-protocol-mcp-servers-in-2025)
- **Tasks Alignment**: Servers cover all project steps, ensuring efficient crawling, scraping, storage, and NLP preparation.
