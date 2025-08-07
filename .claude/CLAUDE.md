# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an arXiv Paper Scraper Project that collects academic papers, books, and articles from multiple sources (arXiv, Project Gutenberg, academic journals) using a multi-agent architecture. The system stores metadata in MongoDB and downloads PDF files within a 300GB storage constraint.

## Core Architecture

The project uses a **multi-agent orchestrator pattern** with specialized agents coordinated by a Main Orchestrator:

### Agent Structure

- **Main Orchestrator**: Central coordinator for task routing and workflow management
- **Crawler Agent**: Discovers content from APIs and websites (arXiv API, Project Gutenberg catalogs)
- **Scraper Agent**: Extracts structured metadata from discovered content
- **Database Agent**: MongoDB operations, schema management, and data storage
- **Downloader Agent**: PDF file downloads with rate limiting and storage management
- **Code Optimization Agent**: Performance analysis and system optimization
- **Testing Agent**: System validation and quality assurance
- **Deployment Agent**: Production deployment and monitoring setup
- **Multi-Source Agent**: Integration of new content sources beyond arXiv
- **NLP Agent**: Data preparation for machine learning applications
- **Monitoring & Reliability Agent**: System observability and error recovery

### Key Directories

- `arxiv_scraper/` - Core application modules organized by function
  - `config/` - Configuration and secrets management
  - `crawler/` - Content discovery and API interaction
  - `scraper/` - Content parsing and metadata extraction
  - `database/` - MongoDB operations and schema
  - `utils/` - Shared utilities (HTTP client, rate limiter, logger)
- `assets/helper_repos/` - Reference implementations from existing scraping libraries
- `init_instruction_set/` - Agent specifications and project planning documents

## Development Commands

**Note**: The main project files (main.py, requirements.txt, README.md) are currently empty. Development commands will be established as the project is implemented.

Common development tasks will likely include:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main scraper
python main.py

# Run tests
python -m pytest tests/

# Start MongoDB (if running locally)
mongod

# Check system status
python -c "from arxiv_scraper.utils.logger import get_logger; get_logger().info('System check')"
```

## System Constraints

- **Storage Limit**: 300GB total allocation for downloaded files
- **Rate Limiting**: arXiv API requires 3-second delays between requests
- **Server Resources**: Designed for 4-core MCP servers
- **Database**: MongoDB for metadata storage with flexible schema design

## Agent Coordination

When working on tasks, follow the agent delegation matrix:

| Task Type | Primary Agent | Supporting Agents |
|-----------|---------------|------------------|
| Content discovery | Crawler Agent | Scraper, Database |
| Performance issues | Code Optimization Agent | Testing, relevant component agents |
| New data sources | Multi-Source Agent | Crawler, Scraper, Database |
| Data export/ML prep | NLP Agent | Database, Testing |
| Production deployment | Deployment Agent | Database, Testing, Code Optimization |
| System reliability | Monitoring & Reliability Agent | All agents |

## Error Handling Strategy

- **Level 1**: Individual agents handle routine errors independently
- **Level 2**: Main Agent coordinates between agents for complex issues
- **Level 3**: Full system analysis via Testing Agent and Monitoring & Reliability Agent

## Data Quality Standards

- MongoDB schema supports multiple content types (papers, books, articles)
- Consistent core fields: title, authors, abstract, date_published, pdf_url
- Source-specific metadata in flexible fields
- Validation rules for completeness and accuracy
- File integrity verification for downloaded PDFs

## Development Best Practices

- Implement proper rate limiting for all external API calls
- Use async/await patterns for concurrent operations
- Include comprehensive error handling and logging
- Maintain data lineage and processing history
- Design for graceful degradation when components fail
- Test with small datasets before full-scale operations
