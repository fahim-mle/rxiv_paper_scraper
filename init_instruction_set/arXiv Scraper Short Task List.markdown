# arXiv Scraper Short Task List

- Set up Python environment and install libraries.
- Install MongoDB on Ubuntu and create `arxiv_papers` database.
- Clone GitHub repos (e.g., `arxivscraper`, `paperscraper`) to `assets/repos/`.
- Configure arXiv MCP Server for API queries.
- Build async crawler using `aiohttp` for arXiv and other sources.
- Scrape metadata with `BeautifulSoup` and store in MongoDB.
- Download PDFs to `./papers/` using Playwright MCP Server.
- Optimize performance with `asyncio` on 4-core MCP servers.
- Extend scraper for books and articles using Fetch MCP Server.
- Process PDFs for NLP with Unstructured MCP Server.
- Test scraper on 100 papers and 10 books/articles.
- Deploy with Docker and schedule daily runs via PiloTY MCP Server.
- Export MongoDB data to JSON for NLP/ML tasks.