# Verbose Task List for arXiv Scraper Project

This document provides a detailed, step-by-step task list for the arXiv Scraper project, based on the provided project plans and documentation. Before installing or setting up anything, first check if it's already done or available.

## 1. Set up Python environment and install libraries

* **Action:** Install Python 3.10 or newer on your development machine.
* **Action:** Create a virtual environment for the project to manage dependencies:

    ```bash
    python -m venv venv
    ```

* **Action:** Activate the virtual environment:
  * **macOS/Linux:** `source venv/bin/activate`
  * **Windows:** `.\venv\Scripts\activate`
* **Action:** Install the necessary Python libraries using pip:

    ```bash
    pip install pymongo aiohttp arxiv beautifulsoup4
    ```

## 2. Install MongoDB on Ubuntu and create `arxiv_papers` database

* **Action:** Install the MongoDB server on your Ubuntu machine:

    ```bash
    sudo apt update
    sudo apt install mongodb
    ```

* **Action:** Start and enable the MongoDB service to ensure it runs on startup:

    ```bash
    sudo systemctl start mongodb
    sudo systemctl enable mongodb
    ```

* **Action:** Connect to the MongoDB shell to create the database and collections:

    ```bash
    mongosh
    ```

* **Action:** Inside the MongoDB shell, create the database and collections:

    ```javascript
    use arxiv_papers;
    db.createCollection("papers");
    db.createCollection("articles");
    ```

## 3. Clone GitHub repos to `assets/repos/`

* **Action:** Create a directory to store the cloned repositories:

    ```bash
    mkdir -p assets/repos
    ```

* **Action:** Clone the specified GitHub repositories into the `assets/repos` directory for analysis:

    ```bash
    git clone https://github.com/Mahdisadjadi/arxivscraper.git assets/repos/arxivscraper
    git clone https://github.com/jannisborn/paperscraper.git assets/repos/paperscraper
    ```

## 4. Configure arXiv MCP Server for API queries

* **Action:** Deploy the `blazickjp/arxiv-mcp-server` Docker container. Refer to the documentation for specific deployment instructions.
* **Action:** Configure the server to use your 300GB storage volume by setting the `--storage-path` argument.
* **Action:** Perform a test query to the server to validate the setup. For example, you can use a tool like `curl` or a simple Python script to make a call to the server's API.

## 5. Build async crawler using `aiohttp` for arXiv and other sources

* **Action:** Create a new Python script, for example, `crawler.py`.
* **Action:** Implement the core crawling logic using the `aiohttp` library for making asynchronous HTTP requests to the arXiv API.
* **Action:** Add functionality to handle pagination of the arXiv API results to ensure all relevant papers are retrieved.
* **Action:** Extend the crawler to fetch data from other sources, such as Project Gutenberg, by making requests to their respective websites.

## 6. Scrape metadata with `BeautifulSoup` and store in MongoDB

* **Action:** Use the `BeautifulSoup` library to parse the HTML or XML data returned by the crawler.
* **Action:** Extract the required metadata fields: title, authors, abstract, and PDF URL.
* **Action:** Establish a connection to your MongoDB database from your Python script.
* **Action:** Insert the scraped metadata into the `papers` collection in the `arxiv_papers` database.

## 7. Download PDFs to `./papers/` using Playwright MCP Server

* **Action:** Deploy the `modelcontextprotocol/servers` Playwright MCP server.
* **Action:** Configure the server to use proxy rotation to avoid being blocked.
* **Action:** Implement the PDF downloading logic using `aiohttp` for asynchronous downloads.
* **Action:** Add rate limiting to your download requests to comply with the terms of service of the websites you are scraping.
* **Action:** Organize the downloaded PDFs by storing them in a directory structure like `./papers/<category>/<paper_id>.pdf`.

## 8. Optimize performance with `asyncio` on 4-core MCP servers

* **Action:** Refactor the crawler and scraper code to make full use of `asyncio` and `concurrent.futures` for parallel execution.
* **Action:** If you have access to multiple MCP servers, distribute the scraping and downloading tasks across them to improve performance.
* **Action:** Implement a caching mechanism to store the results of API queries, reducing the number of redundant requests.

## 9. Extend scraper for books and articles using Fetch MCP Server

* **Action:** Deploy the `modelcontextprotocol/servers` Fetch MCP server.
* **Action:** Add logic to the scraper to handle the structure of book data from Project Gutenberg and articles from open-access journals.
* **Action:** Modify the MongoDB schema to be flexible enough to store the different metadata fields for books and articles (e.g., ISBN, DOI).

## 10. Process PDFs for NLP with Unstructured MCP Server

* **Action:** Deploy the `unstructured-io/unstructured` MCP server.
* **Action:** Create a new script or extend the existing one to use the Unstructured MCP server to process the downloaded PDFs.
* **Action:** Extract the raw text and any other structured data from the PDFs.
* **Action:** Store the processed data in a new collection in MongoDB, for example, `processed_papers`, for use in NLP tasks.

## 11. Test scraper on 100 papers and 10 books/articles

* **Action:** Create a test suite for your scraper.
* **Action:** Run the scraper on a small, controlled dataset of 100 papers and 10 books/articles.
* **Action:** Write assertions to verify that the metadata is correctly extracted and stored in MongoDB.
* **Action:** Check that the PDF files are downloaded correctly and are not corrupted.
* **Action:** Monitor the CPU and memory usage of your servers during the test run.

## 12. Deploy with Docker and schedule daily runs via PiloTY MCP Server

* **Action:** Deploy the `pilotymcp/piloty` MCP server.
* **Action:** Write a `Dockerfile` to containerize your scraper application.
* **Action:** Use PiloTY to schedule a daily cron job that runs your scraper.
* **Action:** Configure a logging solution to capture the output of your scraper, including any errors or warnings.

## 13. Export MongoDB data to JSON for NLP/ML tasks

* **Action:** Write a script to export the data from the `papers` and `articles` collections in MongoDB to a JSON file.
* **Action:** Ensure the JSON output is well-structured and compatible with common NLP libraries like `nltk` and `transformers`.
* **Action:** Create a separate document that describes the schema of the exported JSON file.
