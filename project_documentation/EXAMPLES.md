# Practical Examples

**Ready-to-use code examples for different research scenarios**

This guide provides complete, copy-paste examples for common research tasks. All examples assume you've completed the [Quick Start](QUICK_START.md) setup.

## 📚 Table of Contents

- [Basic Scraping Examples](#-basic-scraping-examples)
- [Data Analysis Examples](#-data-analysis-examples)
- [Export & Integration Examples](#-export--integration-examples)
- [Automation Examples](#-automation-examples)
- [Advanced Analysis Examples](#-advanced-analysis-examples)
- [Custom Agent Examples](#-custom-agent-examples)

---

## 🚀 Basic Scraping Examples

### Example 1: Download Papers on Specific Topics

**Scenario**: PhD student researching computer vision needs recent papers on object detection.

```bash
#!/bin/bash
# download_cv_papers.sh

echo "Downloading Computer Vision papers..."

# Recent object detection papers
python main.py \
  --keywords "object detection,YOLO,R-CNN,detection transformer" \
  --categories "cs.CV" \
  --max-papers 100 \
  --days-back 180 \
  --download-pdfs \
  --log-level INFO \
  --log-file cv_scraping.log

echo "Download complete! Check papers/arxiv/ for PDFs"

# Quick summary
python -c "
from arxiv_scraper.database.mongodb_operations import get_operations
db_ops = get_operations()
cv_papers = list(db_ops.search_papers_by_keyword('object detection'))
print(f'Found {len(cv_papers)} object detection papers')
"
```

**Expected output**:

```
Papers crawled:    85
Papers processed:  85
Papers stored:     85
PDFs downloaded:   82
Download size:     267.4MB
Found 85 object detection papers
```

### Example 2: Multi-Category Research Survey

**Scenario**: Researcher studying AI applications across multiple domains.

```python
#!/usr/bin/env python3
# multi_category_survey.py

import asyncio
from arxiv_scraper.crawler.arxiv_api import ArxivCrawler
from arxiv_scraper.database.mongodb_operations import get_operations

async def survey_ai_applications():
    """Collect AI papers from multiple categories for survey."""

    # Research categories of interest
    survey_categories = {
        'ai_theory': ['cs.AI', 'cs.LG'],
        'computer_vision': ['cs.CV'],
        'nlp': ['cs.CL'],
        'robotics': ['cs.RO'],
        'hci': ['cs.HC'],
        'graphics': ['cs.GR']
    }

    crawler = ArxivCrawler(rate_limit_delay=3.0)
    db_ops = get_operations()

    all_papers = {}

    for domain, categories in survey_categories.items():
        print(f"\\n📡 Collecting {domain} papers...")

        papers = await crawler.crawl_specific_categories(
            categories=categories,
            max_papers=150,
            days_back=365  # Last year
        )

        all_papers[domain] = papers
        print(f"✅ Collected {len(papers)} papers for {domain}")

        # Store in database with domain tags
        for paper in papers:
            paper['research_domain'] = domain

        if papers:
            result = db_ops.bulk_insert_papers(papers)
            print(f"   Stored: {result['inserted']}, Errors: {result['errors']}")

    # Generate survey summary
    print(f"\\n📊 SURVEY COLLECTION SUMMARY")
    print("=" * 40)

    total_papers = sum(len(papers) for papers in all_papers.values())
    print(f"Total papers collected: {total_papers}")

    for domain, papers in all_papers.items():
        print(f"  {domain}: {len(papers)} papers")

    return all_papers

if __name__ == "__main__":
    results = asyncio.run(survey_ai_applications())
```

**Usage**:

```bash
chmod +x multi_category_survey.py
python multi_category_survey.py
```

### Example 3: Targeted Author Collection

**Scenario**: Following specific research groups and prolific authors.

```python
#!/usr/bin/env python3
# author_tracking.py

import asyncio
import re
from arxiv_scraper.database.mongodb_operations import get_operations

# Target research groups and key authors
TARGET_GROUPS = {
    'OpenAI': ['openai'],
    'DeepMind': ['deepmind', 'google deepmind'],
    'Meta AI': ['meta ai', 'facebook ai'],
    'Stanford HAI': ['stanford'],
    'MIT CSAIL': ['mit', 'csail'],
    'UC Berkeley': ['berkeley', 'uc berkeley']
}

NOTABLE_AUTHORS = [
    'Geoffrey Hinton', 'Yann LeCun', 'Yoshua Bengio',
    'Andrej Karpathy', 'Pieter Abbeel', 'Sergey Levine',
    'Chelsea Finn', 'Ilya Sutskever', 'Dario Amodei'
]

async def track_research_groups():
    """Track papers from specific research groups."""

    db_ops = get_operations()

    # Search by group affiliations in abstracts/titles
    group_papers = {}

    for group, keywords in TARGET_GROUPS.items():
        papers = []
        for keyword in keywords:
            # Search in abstracts for mentions of the group
            results = list(db_ops.find_papers({
                '$or': [
                    {'abstract': {'$regex': keyword, '$options': 'i'}},
                    {'title': {'$regex': keyword, '$options': 'i'}}
                ]
            }))
            papers.extend(results)

        # Remove duplicates
        unique_papers = {p['paper_id']: p for p in papers}.values()
        group_papers[group] = list(unique_papers)

        print(f"🏢 {group}: {len(group_papers[group])} papers")

    # Track specific authors
    author_papers = {}

    for author in NOTABLE_AUTHORS:
        # Search by author name (exact match in authors list)
        papers = list(db_ops.find_papers({
            'authors': {'$regex': re.escape(author), '$options': 'i'}
        }))

        if papers:
            author_papers[author] = papers
            print(f"👤 {author}: {len(papers)} papers")

    # Generate research group report
    with open('research_group_report.md', 'w') as f:
        f.write('# Research Group Activity Report\\n\\n')

        f.write('## Research Groups\\n\\n')
        for group, papers in group_papers.items():
            f.write(f'### {group} ({len(papers)} papers)\\n\\n')
            for paper in papers[:5]:  # Top 5 papers
                f.write(f'- **{paper["title"]}**\\n')
                f.write(f'  - Authors: {", ".join(paper["authors"][:3])}\\n')
                f.write(f'  - Date: {paper["date_published"][:10]}\\n')
                f.write(f'  - arXiv: {paper["paper_id"]}\\n\\n')

        f.write('## Notable Authors\\n\\n')
        for author, papers in author_papers.items():
            f.write(f'### {author} ({len(papers)} papers)\\n\\n')
            for paper in papers[:3]:  # Top 3 papers
                f.write(f'- **{paper["title"]}**\\n')
                f.write(f'  - Date: {paper["date_published"][:10]}\\n\\n')

    print("\\n📝 Report saved to research_group_report.md")
    return group_papers, author_papers

if __name__ == "__main__":
    groups, authors = asyncio.run(track_research_groups())
```

---

## 📊 Data Analysis Examples

### Example 4: Research Trend Analysis

**Scenario**: Analyzing how research topics have evolved over time.

```python
#!/usr/bin/env python3
# trend_analysis.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from datetime import datetime, timedelta
from arxiv_scraper.database.mongodb_operations import get_operations

def analyze_research_trends():
    """Comprehensive research trend analysis."""

    print("🔍 Loading papers from database...")
    db_ops = get_operations()

    # Get papers from last 3 years for trend analysis
    papers = list(db_ops.find_papers({
        'date_published': {'$gte': '2021-01-01'}
    }))

    if not papers:
        print("❌ No papers found. Run the scraper first!")
        return

    print(f"📊 Analyzing {len(papers)} papers...")

    # Convert to DataFrame
    df = pd.DataFrame(papers)
    df['date_published'] = pd.to_datetime(df['date_published'])
    df['year'] = df['date_published'].dt.year
    df['month'] = df['date_published'].dt.month
    df['year_month'] = df['date_published'].dt.to_period('M')

    # 1. Papers per month trend
    plt.figure(figsize=(15, 10))

    plt.subplot(2, 2, 1)
    monthly_counts = df.groupby('year_month').size()
    monthly_counts.plot(kind='line', marker='o')
    plt.title('Papers Published Per Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Papers')
    plt.xticks(rotation=45)

    # 2. Top categories over time
    plt.subplot(2, 2, 2)

    # Get top 5 categories
    all_categories = []
    for cats in df['categories']:
        all_categories.extend(cats)
    top_categories = [cat for cat, _ in Counter(all_categories).most_common(5)]

    # Plot category trends
    for category in top_categories:
        cat_data = []
        for month in monthly_counts.index:
            month_papers = df[df['year_month'] == month]
            count = sum(1 for paper in month_papers.itertuples()
                       if category in paper.categories)
            cat_data.append(count)

        plt.plot(monthly_counts.index.astype(str), cat_data,
                marker='o', label=category, linewidth=2)

    plt.title('Category Trends Over Time')
    plt.xlabel('Month')
    plt.ylabel('Papers per Category')
    plt.legend()
    plt.xticks(rotation=45)

    # 3. Abstract length analysis
    plt.subplot(2, 2, 3)
    df['abstract_length'] = df['abstract'].str.len()

    yearly_abstract_length = df.groupby('year')['abstract_length'].mean()
    yearly_abstract_length.plot(kind='bar')
    plt.title('Average Abstract Length by Year')
    plt.xlabel('Year')
    plt.ylabel('Characters')

    # 4. Author collaboration trends
    plt.subplot(2, 2, 4)
    df['num_authors'] = df['authors'].apply(len)
    yearly_authors = df.groupby('year')['num_authors'].mean()
    yearly_authors.plot(kind='bar', color='green')
    plt.title('Average Authors per Paper by Year')
    plt.xlabel('Year')
    plt.ylabel('Number of Authors')

    plt.tight_layout()
    plt.savefig('research_trends.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Generate detailed statistics
    stats = {
        'total_papers': len(df),
        'date_range': f"{df['date_published'].min().date()} to {df['date_published'].max().date()}",
        'top_categories': dict(Counter(all_categories).most_common(10)),
        'papers_per_year': df['year'].value_counts().sort_index().to_dict(),
        'avg_abstract_length': df['abstract_length'].mean(),
        'avg_authors_per_paper': df['num_authors'].mean()
    }

    print("\\n📈 TREND ANALYSIS RESULTS")
    print("=" * 40)
    print(f"Total papers: {stats['total_papers']}")
    print(f"Date range: {stats['date_range']}")
    print(f"Average abstract length: {stats['avg_abstract_length']:.0f} characters")
    print(f"Average authors per paper: {stats['avg_authors_per_paper']:.1f}")

    print("\\n📋 Top 5 Categories:")
    for i, (cat, count) in enumerate(list(stats['top_categories'].items())[:5], 1):
        print(f"{i:2d}. {cat}: {count} papers")

    print("\\n📅 Papers by Year:")
    for year, count in sorted(stats['papers_per_year'].items()):
        print(f"  {year}: {count} papers")

    return stats

if __name__ == "__main__":
    stats = analyze_research_trends()
```

### Example 5: Author Network Analysis

**Scenario**: Understanding collaboration patterns in research.

```python
#!/usr/bin/env python3
# collaboration_network.py

import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from itertools import combinations
from collections import defaultdict
from arxiv_scraper.database.mongodb_operations import get_operations

def analyze_collaboration_network():
    """Analyze author collaboration networks."""

    print("🕸️ Building collaboration network...")
    db_ops = get_operations()

    # Get recent papers with multiple authors
    papers = list(db_ops.find_papers({
        'date_published': {'$gte': '2023-01-01'},
        'authors': {'$exists': True, '$not': {'$size': 0}}
    }))

    if not papers:
        print("❌ No papers found. Run the scraper first!")
        return

    # Build collaboration graph
    G = nx.Graph()
    author_stats = defaultdict(int)

    for paper in papers:
        authors = paper.get('authors', [])

        # Count papers per author
        for author in authors:
            author_stats[author] += 1

        # Add collaboration edges
        if len(authors) > 1:
            for author1, author2 in combinations(authors, 2):
                if G.has_edge(author1, author2):
                    G[author1][author2]['weight'] += 1
                else:
                    G.add_edge(author1, author2, weight=1)

    print(f"📊 Network statistics:")
    print(f"  Authors: {G.number_of_nodes()}")
    print(f"  Collaborations: {G.number_of_edges()}")

    # Find most prolific authors
    top_authors = sorted(author_stats.items(), key=lambda x: x[1], reverse=True)[:20]

    print(f"\\n👥 Top 20 Most Prolific Authors:")
    for i, (author, count) in enumerate(top_authors, 1):
        print(f"{i:2d}. {author}: {count} papers")

    # Network centrality analysis
    if G.number_of_nodes() > 0:
        degree_centrality = nx.degree_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)

        # Top central authors
        top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        top_closeness = sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]

        print(f"\\n🎯 Most Connected Authors (Degree Centrality):")
        for i, (author, centrality) in enumerate(top_degree, 1):
            print(f"{i:2d}. {author}: {centrality:.3f}")

        print(f"\\n🌉 Bridge Authors (Betweenness Centrality):")
        for i, (author, centrality) in enumerate(top_betweenness, 1):
            print(f"{i:2d}. {author}: {centrality:.3f}")

        # Visualize network (subset for clarity)
        plt.figure(figsize=(15, 10))

        # Create subgraph with most connected authors
        top_author_names = [author for author, _ in top_authors[:50]]
        subgraph = G.subgraph(top_author_names)

        # Node sizes based on number of papers
        node_sizes = [author_stats[author] * 20 for author in subgraph.nodes()]

        # Edge widths based on collaboration frequency
        edge_widths = [subgraph[u][v]['weight'] for u, v in subgraph.edges()]

        # Layout
        pos = nx.spring_layout(subgraph, k=1, iterations=50)

        # Draw network
        nx.draw_networkx_nodes(subgraph, pos, node_size=node_sizes,
                              node_color='lightblue', alpha=0.7)
        nx.draw_networkx_edges(subgraph, pos, width=edge_widths,
                              alpha=0.5, edge_color='gray')

        # Add labels for most central nodes
        top_central_names = [author for author, _ in top_degree[:10]]
        labels = {node: node.split()[-1] if len(node.split()) > 1 else node
                 for node in subgraph.nodes() if node in top_central_names}
        nx.draw_networkx_labels(subgraph, pos, labels, font_size=8)

        plt.title('Author Collaboration Network\\n(Node size = papers, Edge width = collaborations)')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('collaboration_network.png', dpi=300, bbox_inches='tight')
        plt.show()

        # Export collaboration data
        collaboration_data = []
        for u, v, data in G.edges(data=True):
            collaboration_data.append({
                'author1': u,
                'author2': v,
                'collaborations': data['weight'],
                'author1_papers': author_stats[u],
                'author2_papers': author_stats[v]
            })

        collab_df = pd.DataFrame(collaboration_data)
        collab_df = collab_df.sort_values('collaborations', ascending=False)
        collab_df.to_csv('author_collaborations.csv', index=False)

        print(f"\\n💾 Exported collaboration data to author_collaborations.csv")
        print(f"📊 Network visualization saved as collaboration_network.png")

    return G, author_stats

if __name__ == "__main__":
    network, stats = analyze_collaboration_network()
```

---

## 💾 Export & Integration Examples

### Example 6: Export for Citation Managers

**Scenario**: Generate bibliography files for Zotero, Mendeley, etc.

```python
#!/usr/bin/env python3
# export_citations.py

import json
import csv
from datetime import datetime
from arxiv_scraper.database.mongodb_operations import get_operations

def export_to_bibtex(papers, filename='bibliography.bib'):
    """Export papers to BibTeX format."""

    with open(filename, 'w', encoding='utf-8') as f:
        for paper in papers:
            # Clean up paper_id for BibTeX key
            bibtex_key = paper['paper_id'].replace('.', '_').replace('v', '_v')

            # Format authors
            authors = ' and '.join(paper.get('authors', ['Unknown']))

            # Extract year
            year = paper.get('date_published', '')[:4] if paper.get('date_published') else 'unknown'

            # Primary category
            primary_category = paper.get('categories', [''])[0] if paper.get('categories') else ''

            bibtex_entry = f"""@article{{{bibtex_key},
    title = {{{paper.get('title', 'Untitled')}}},
    author = {{{authors}}},
    year = {{{year}}},
    eprint = {{{paper['paper_id']}}},
    archivePrefix = {{arXiv}},
    primaryClass = {{{primary_category}}},
    abstract = {{{paper.get('abstract', '')[:500]}...}},
    url = {{https://arxiv.org/abs/{paper['paper_id']}}},
    note = {{Available at: https://arxiv.org/abs/{paper['paper_id']}}}
}}

"""
            f.write(bibtex_entry)

    print(f"📚 Exported {len(papers)} papers to {filename}")

def export_to_endnote(papers, filename='bibliography.enw'):
    """Export papers to EndNote format."""

    with open(filename, 'w', encoding='utf-8') as f:
        for paper in papers:
            year = paper.get('date_published', '')[:4] if paper.get('date_published') else ''

            endnote_entry = f"""%0 Journal Article
%T {paper.get('title', 'Untitled')}
%D {year}
%X {paper.get('abstract', '')}
%U https://arxiv.org/abs/{paper['paper_id']}
%K {', '.join(paper.get('categories', []))}
"""

            # Add authors
            for author in paper.get('authors', []):
                endnote_entry += f"%A {author}\\n"

            endnote_entry += "\\n"
            f.write(endnote_entry)

    print(f"📝 Exported {len(papers)} papers to {filename}")

def export_to_ris(papers, filename='bibliography.ris'):
    """Export papers to RIS format (Reference Manager)."""

    with open(filename, 'w', encoding='utf-8') as f:
        for paper in papers:
            year = paper.get('date_published', '')[:4] if paper.get('date_published') else ''

            ris_entry = f"""TY  - JOUR
TI  - {paper.get('title', 'Untitled')}
PY  - {year}
AB  - {paper.get('abstract', '')}
UR  - https://arxiv.org/abs/{paper['paper_id']}
"""

            # Add authors
            for author in paper.get('authors', []):
                ris_entry += f"AU  - {author}\\n"

            # Add keywords
            for category in paper.get('categories', []):
                ris_entry += f"KW  - {category}\\n"

            ris_entry += "ER  - \\n\\n"
            f.write(ris_entry)

    print(f"🔗 Exported {len(papers)} papers to {filename}")

def export_to_csv(papers, filename='papers_export.csv'):
    """Export papers to CSV format."""

    fieldnames = ['paper_id', 'title', 'authors', 'abstract', 'categories',
                 'date_published', 'pdf_url', 'arxiv_url']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for paper in papers:
            row = {
                'paper_id': paper['paper_id'],
                'title': paper.get('title', ''),
                'authors': '; '.join(paper.get('authors', [])),
                'abstract': paper.get('abstract', ''),
                'categories': '; '.join(paper.get('categories', [])),
                'date_published': paper.get('date_published', ''),
                'pdf_url': paper.get('pdf_url', ''),
                'arxiv_url': f"https://arxiv.org/abs/{paper['paper_id']}"
            }
            writer.writerow(row)

    print(f"📊 Exported {len(papers)} papers to {filename}")

def main():
    """Export papers in multiple formats."""

    print("📤 Starting bibliography export...")
    db_ops = get_operations()

    # Get papers (customize query as needed)
    papers = list(db_ops.find_papers({
        # Example: papers from last year
        'date_published': {'$gte': '2023-01-01'}
    }))

    if not papers:
        print("❌ No papers found. Run the scraper first!")
        return

    print(f"📚 Found {len(papers)} papers to export")

    # Export in multiple formats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    export_to_bibtex(papers, f'papers_bibtex_{timestamp}.bib')
    export_to_endnote(papers, f'papers_endnote_{timestamp}.enw')
    export_to_ris(papers, f'papers_ris_{timestamp}.ris')
    export_to_csv(papers, f'papers_data_{timestamp}.csv')

    # Create import instructions
    with open(f'import_instructions_{timestamp}.md', 'w') as f:
        f.write(f"""# Bibliography Import Instructions

## Files Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Total papers exported: {len(papers)}

### Zotero
1. File → Import → Select `papers_bibtex_{timestamp}.bib`
2. Or use RIS format: `papers_ris_{timestamp}.ris`

### Mendeley
1. File → Import → BibTeX → Select `papers_bibtex_{timestamp}.bib`
2. Or File → Import → RIS → Select `papers_ris_{timestamp}.ris`

### EndNote
1. File → Import → Select `papers_endnote_{timestamp}.enw`
2. Choose "Reference Manager (RIS)" as import option

### RefWorks
1. Import → References → Upload → Select `papers_ris_{timestamp}.ris`

### Data Analysis
- Use `papers_data_{timestamp}.csv` for spreadsheet analysis
- Contains all metadata in tabular format

## Notes
- All URLs point to arXiv abstracts
- PDFs can be downloaded directly from arXiv
- Categories are included as keywords/tags
""")

    print(f"\\n✅ Export complete! Files saved with timestamp {timestamp}")
    print(f"📋 See import_instructions_{timestamp}.md for usage instructions")

if __name__ == "__main__":
    main()
```

### Example 7: Machine Learning Dataset Preparation

**Scenario**: Prepare data for NLP research and model training.

```python
#!/usr/bin/env python3
# ml_dataset_prep.py

import pandas as pd
import numpy as np
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from collections import Counter
import re
from arxiv_scraper.database.mongodb_operations import get_operations

def clean_text(text):
    """Clean and normalize text for ML processing."""
    if not text:
        return ""

    # Remove special characters and normalize whitespace
    text = re.sub(r'[^a-zA-Z0-9\\s]', ' ', text)
    text = re.sub(r'\\s+', ' ', text)
    text = text.strip().lower()

    return text

def create_classification_dataset():
    """Create dataset for paper category classification."""

    print("🤖 Preparing classification dataset...")
    db_ops = get_operations()

    # Get papers with abstracts and categories
    papers = list(db_ops.find_papers({
        'abstract': {'$exists': True, '$ne': ''},
        'categories': {'$exists': True, '$not': {'$size': 0}}
    }))

    if not papers:
        print("❌ No suitable papers found!")
        return None

    print(f"📊 Processing {len(papers)} papers...")

    # Prepare classification data
    classification_data = []

    for paper in papers:
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')

        # Combine title and abstract
        text = f"{title}. {abstract}"
        text = clean_text(text)

        # Create samples for each category
        for category in paper.get('categories', []):
            if len(text.split()) > 20:  # Filter very short texts
                classification_data.append({
                    'text': text,
                    'category': category,
                    'paper_id': paper['paper_id'],
                    'title': title,
                    'text_length': len(text),
                    'word_count': len(text.split())
                })

    df = pd.DataFrame(classification_data)

    # Filter categories with sufficient samples
    category_counts = df['category'].value_counts()
    min_samples = 50  # Minimum samples per category
    valid_categories = category_counts[category_counts >= min_samples].index

    df_filtered = df[df['category'].isin(valid_categories)]

    print(f"📋 Dataset statistics:")
    print(f"  Total samples: {len(df_filtered)}")
    print(f"  Categories: {len(valid_categories)}")
    print(f"  Average text length: {df_filtered['text_length'].mean():.0f} chars")
    print(f"  Average word count: {df_filtered['word_count'].mean():.0f} words")

    # Split dataset
    X = df_filtered[['text', 'paper_id', 'title']]
    y = df_filtered['category']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Create train/test datasets
    train_df = X_train.copy()
    train_df['category'] = y_train

    test_df = X_test.copy()
    test_df['category'] = y_test

    # Save datasets
    train_df.to_csv('arxiv_classification_train.csv', index=False)
    test_df.to_csv('arxiv_classification_test.csv', index=False)

    # Save category mapping
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(df_filtered['category'])

    category_mapping = {
        'categories': list(label_encoder.classes_),
        'category_counts': dict(category_counts[valid_categories]),
        'encoding': {cat: int(label_encoder.transform([cat])[0])
                    for cat in label_encoder.classes_}
    }

    with open('category_mapping.json', 'w') as f:
        json.dump(category_mapping, f, indent=2)

    print(f"\\n✅ Classification dataset saved:")
    print(f"  Training: {len(train_df)} samples")
    print(f"  Testing: {len(test_df)} samples")
    print(f"  Categories: {len(valid_categories)}")

    return train_df, test_df, category_mapping

def create_similarity_dataset():
    """Create dataset for paper similarity/recommendation tasks."""

    print("🔗 Preparing similarity dataset...")
    db_ops = get_operations()

    papers = list(db_ops.find_papers({
        'abstract': {'$exists': True, '$ne': ''},
        'title': {'$exists': True, '$ne': ''}
    }))

    similarity_data = []

    for paper in papers:
        similarity_data.append({
            'paper_id': paper['paper_id'],
            'title': paper.get('title', ''),
            'abstract': clean_text(paper.get('abstract', '')),
            'categories': '|'.join(paper.get('categories', [])),
            'authors': '|'.join(paper.get('authors', [])),
            'date_published': paper.get('date_published', ''),
            'embedding_text': clean_text(f"{paper.get('title', '')}. {paper.get('abstract', '')}")
        })

    sim_df = pd.DataFrame(similarity_data)
    sim_df.to_csv('arxiv_similarity_dataset.csv', index=False)

    print(f"✅ Similarity dataset saved: {len(sim_df)} papers")
    return sim_df

def create_temporal_dataset():
    """Create dataset for temporal analysis and trend prediction."""

    print("📅 Preparing temporal dataset...")
    db_ops = get_operations()

    papers = list(db_ops.find_papers({
        'date_published': {'$exists': True, '$ne': ''}
    }))

    temporal_data = []

    for paper in papers:
        date_pub = paper.get('date_published', '')
        if date_pub:
            try:
                pub_date = pd.to_datetime(date_pub)

                temporal_data.append({
                    'paper_id': paper['paper_id'],
                    'title': paper.get('title', ''),
                    'date_published': date_pub,
                    'year': pub_date.year,
                    'month': pub_date.month,
                    'day': pub_date.day,
                    'weekday': pub_date.weekday(),
                    'categories': '|'.join(paper.get('categories', [])),
                    'primary_category': paper.get('categories', ['unknown'])[0],
                    'num_authors': len(paper.get('authors', [])),
                    'abstract_length': len(paper.get('abstract', '')),
                    'title_length': len(paper.get('title', ''))
                })
            except:
                continue

    temp_df = pd.DataFrame(temporal_data)
    temp_df = temp_df.sort_values('date_published')
    temp_df.to_csv('arxiv_temporal_dataset.csv', index=False)

    print(f"✅ Temporal dataset saved: {len(temp_df)} papers")
    return temp_df

def create_author_dataset():
    """Create dataset for author analysis and collaboration prediction."""

    print("👥 Preparing author dataset...")
    db_ops = get_operations()

    papers = list(db_ops.find_papers({
        'authors': {'$exists': True, '$not': {'$size': 0}}
    }))

    author_papers = []
    author_collaborations = []

    # Author-paper relationships
    for paper in papers:
        for author in paper.get('authors', []):
            author_papers.append({
                'author': author,
                'paper_id': paper['paper_id'],
                'title': paper.get('title', ''),
                'date_published': paper.get('date_published', ''),
                'categories': '|'.join(paper.get('categories', [])),
                'num_coauthors': len(paper.get('authors', [])) - 1
            })

    # Author collaboration network
    from itertools import combinations
    for paper in papers:
        authors = paper.get('authors', [])
        if len(authors) > 1:
            for author1, author2 in combinations(authors, 2):
                author_collaborations.append({
                    'author1': author1,
                    'author2': author2,
                    'paper_id': paper['paper_id'],
                    'date_published': paper.get('date_published', ''),
                    'categories': '|'.join(paper.get('categories', []))
                })

    author_df = pd.DataFrame(author_papers)
    collab_df = pd.DataFrame(author_collaborations)

    # Author statistics
    author_stats = author_df.groupby('author').agg({
        'paper_id': 'count',
        'num_coauthors': 'mean',
        'date_published': ['min', 'max']
    }).reset_index()

    author_stats.columns = ['author', 'num_papers', 'avg_coauthors', 'first_paper', 'last_paper']

    author_df.to_csv('arxiv_author_papers.csv', index=False)
    collab_df.to_csv('arxiv_author_collaborations.csv', index=False)
    author_stats.to_csv('arxiv_author_statistics.csv', index=False)

    print(f"✅ Author datasets saved:")
    print(f"  Author-paper relationships: {len(author_df)}")
    print(f"  Collaborations: {len(collab_df)}")
    print(f"  Unique authors: {len(author_stats)}")

    return author_df, collab_df, author_stats

def main():
    """Prepare all ML datasets."""

    print("🚀 Starting ML dataset preparation...")

    # Create different datasets
    datasets = {}

    try:
        datasets['classification'] = create_classification_dataset()
        datasets['similarity'] = create_similarity_dataset()
        datasets['temporal'] = create_temporal_dataset()
        datasets['author'] = create_author_dataset()

        # Create dataset summary
        summary = {
            'created_at': pd.Timestamp.now().isoformat(),
            'datasets': {
                'classification': {
                    'files': ['arxiv_classification_train.csv', 'arxiv_classification_test.csv', 'category_mapping.json'],
                    'description': 'Text classification by arXiv categories'
                },
                'similarity': {
                    'files': ['arxiv_similarity_dataset.csv'],
                    'description': 'Paper similarity and recommendation'
                },
                'temporal': {
                    'files': ['arxiv_temporal_dataset.csv'],
                    'description': 'Time series analysis and trend prediction'
                },
                'author': {
                    'files': ['arxiv_author_papers.csv', 'arxiv_author_collaborations.csv', 'arxiv_author_statistics.csv'],
                    'description': 'Author analysis and collaboration networks'
                }
            }
        }

        with open('dataset_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\\n🎉 All datasets prepared successfully!")
        print(f"📋 See dataset_summary.json for details")

    except Exception as e:
        print(f"❌ Error preparing datasets: {e}")
        return None

    return datasets

if __name__ == "__main__":
    datasets = main()
```

---

## ⚙️ Automation Examples

### Example 8: Automated Daily Research Monitoring

**Scenario**: Set up automated daily alerts for new papers in your field.

```python
#!/usr/bin/env python3
# daily_research_monitor.py

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
from arxiv_scraper.crawler.arxiv_api import ArxivCrawler
from arxiv_scraper.database.mongodb_operations import get_operations

# Configuration
RESEARCH_INTERESTS = {
    'keywords': ['transformer', 'attention mechanism', 'large language model', 'BERT', 'GPT'],
    'categories': ['cs.AI', 'cs.LG', 'cs.CL'],
    'authors': ['Geoffrey Hinton', 'Yann LeCun', 'Yoshua Bengio']  # Optional
}

EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # Update for your email provider
    'smtp_port': 587,
    'email': 'your_email@gmail.com',  # Update with your email
    'password': 'your_app_password',  # Use app password for Gmail
    'recipient': 'your_email@gmail.com'  # Where to send alerts
}

class ResearchMonitor:
    def __init__(self, interests, email_config=None):
        self.interests = interests
        self.email_config = email_config
        self.crawler = ArxivCrawler(rate_limit_delay=3.0)
        self.db_ops = get_operations()

    async def find_new_papers(self, days_back=1):
        """Find new papers matching research interests."""

        print(f"🔍 Searching for papers from last {days_back} days...")

        # Search by categories
        papers = await self.crawler.crawl_specific_categories(
            categories=self.interests['categories'],
            max_papers=100,
            days_back=days_back
        )

        if not papers:
            print("No new papers found in categories")
            return []

        # Filter by keywords and authors
        relevant_papers = []

        for paper in papers:
            relevance_score = 0
            reasons = []

            # Check keywords in title and abstract
            title_abstract = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()

            for keyword in self.interests['keywords']:
                if keyword.lower() in title_abstract:
                    relevance_score += 2
                    reasons.append(f"keyword: {keyword}")

            # Check authors
            paper_authors = [author.lower() for author in paper.get('authors', [])]
            for interest_author in self.interests.get('authors', []):
                if any(interest_author.lower() in paper_author for paper_author in paper_authors):
                    relevance_score += 3
                    reasons.append(f"author: {interest_author}")

            if relevance_score > 0:
                paper['relevance_score'] = relevance_score
                paper['relevance_reasons'] = reasons
                relevant_papers.append(paper)

        # Sort by relevance
        relevant_papers.sort(key=lambda x: x['relevance_score'], reverse=True)

        print(f"✅ Found {len(relevant_papers)} relevant papers")
        return relevant_papers

    def generate_email_report(self, papers):
        """Generate HTML email report."""

        if not papers:
            return "No new relevant papers found today."

        html_content = f"""
        <html>
        <body>
            <h2>📚 Daily Research Alert - {datetime.now().strftime('%Y-%m-%d')}</h2>
            <p>Found <strong>{len(papers)}</strong> relevant papers:</p>
            <hr>
        """

        for i, paper in enumerate(papers[:10], 1):  # Top 10 papers
            relevance_info = ', '.join(paper.get('relevance_reasons', []))
            authors = ', '.join(paper.get('authors', [])[:3])
            if len(paper.get('authors', [])) > 3:
                authors += ' et al.'

            html_content += f"""
            <h3>{i}. {paper.get('title', 'Untitled')}</h3>
            <p><strong>Authors:</strong> {authors}</p>
            <p><strong>Categories:</strong> {', '.join(paper.get('categories', []))}</p>
            <p><strong>Relevance:</strong> {relevance_info} (Score: {paper.get('relevance_score', 0)})</p>
            <p><strong>Abstract:</strong> {paper.get('abstract', '')[:300]}...</p>
            <p><strong>arXiv:</strong> <a href="https://arxiv.org/abs/{paper['paper_id']}">https://arxiv.org/abs/{paper['paper_id']}</a></p>
            <p><strong>PDF:</strong> <a href="{paper.get('pdf_url', '')}">Download PDF</a></p>
            <hr>
            """

        html_content += """
            <p><em>This is an automated research alert. Update your interests in the monitoring script.</em></p>
        </body>
        </html>
        """

        return html_content

    def send_email(self, content, subject):
        """Send email alert."""

        if not self.email_config:
            print("📧 Email not configured, skipping email alert")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config['email']
            msg['To'] = self.email_config['recipient']

            html_part = MIMEText(content, 'html')
            msg.attach(html_part)

            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            server.send_message(msg)
            server.quit()

            print("✅ Email alert sent successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    def save_daily_report(self, papers):
        """Save daily report to file."""

        report_data = {
            'date': datetime.now().isoformat(),
            'total_papers': len(papers),
            'research_interests': self.interests,
            'papers': papers
        }

        filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"💾 Daily report saved to {filename}")
        return filename

async def main():
    """Main monitoring function."""

    print(f"🚀 Starting daily research monitoring - {datetime.now()}")

    # Initialize monitor
    monitor = ResearchMonitor(RESEARCH_INTERESTS, EMAIL_CONFIG)

    # Find new papers
    new_papers = await monitor.find_new_papers(days_back=1)

    if new_papers:
        # Generate and send email report
        email_content = monitor.generate_email_report(new_papers)
        subject = f"📚 Daily Research Alert - {len(new_papers)} papers ({datetime.now().strftime('%Y-%m-%d')})"
        monitor.send_email(email_content, subject)

        # Save daily report
        monitor.save_daily_report(new_papers)

        # Print summary
        print(f"\\n📊 DAILY MONITORING SUMMARY")
        print("=" * 40)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Relevant papers: {len(new_papers)}")
        print(f"Top paper: {new_papers[0].get('title', 'N/A')}")
        print(f"Score: {new_papers[0].get('relevance_score', 0)}")

    else:
        print("📭 No relevant papers found today")

        # Send "no papers" email if configured
        if EMAIL_CONFIG:
            no_papers_content = f"""
            <html>
            <body>
                <h2>📭 Daily Research Alert - {datetime.now().strftime('%Y-%m-%d')}</h2>
                <p>No new papers matching your research interests were found today.</p>
                <p><strong>Monitoring:</strong></p>
                <ul>
                    <li>Categories: {', '.join(RESEARCH_INTERESTS['categories'])}</li>
                    <li>Keywords: {', '.join(RESEARCH_INTERESTS['keywords'])}</li>
                </ul>
                <p><em>This is an automated research alert.</em></p>
            </body>
            </html>
            """
            monitor.send_email(no_papers_content, f"📭 Daily Research Alert - No papers ({datetime.now().strftime('%Y-%m-%d')})")

if __name__ == "__main__":
    asyncio.run(main())
```

**Setup automated daily monitoring:**

```bash
# Make script executable
chmod +x daily_research_monitor.py

# Test the monitoring
python daily_research_monitor.py

# Add to crontab for daily execution at 9 AM
crontab -e
# Add line: 0 9 * * * cd /path/to/arxiv_scraper && python daily_research_monitor.py >> monitoring.log 2>&1
```

---

## 🔬 Advanced Analysis Examples

### Example 9: Research Impact Prediction

**Scenario**: Predict potential impact of papers based on historical patterns.

```python
#!/usr/bin/env python3
# impact_prediction.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from arxiv_scraper.database.mongodb_operations import get_operations

class ImpactPredictor:
    def __init__(self):
        self.db_ops = get_operations()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.label_encoders = {}

    def extract_features(self, papers):
        """Extract features for impact prediction."""

        features = []

        for paper in papers:
            # Basic metadata features
            num_authors = len(paper.get('authors', []))
            num_categories = len(paper.get('categories', []))
            title_length = len(paper.get('title', ''))
            abstract_length = len(paper.get('abstract', ''))

            # Date features
            pub_date = pd.to_datetime(paper.get('date_published', ''))
            pub_year = pub_date.year if pd.notna(pub_date) else 2020
            pub_month = pub_date.month if pd.notna(pub_date) else 1
            pub_weekday = pub_date.weekday() if pd.notna(pub_date) else 0

            # Text analysis features
            abstract = paper.get('abstract', '').lower()
            title = paper.get('title', '').lower()

            # Count important keywords
            impact_keywords = ['novel', 'new', 'improved', 'breakthrough', 'efficient',
                             'sota', 'state-of-the-art', 'outperform', 'significant']
            keyword_count = sum(1 for kw in impact_keywords if kw in abstract or kw in title)

            # Mathematical content indicators
            math_indicators = ['theorem', 'proof', 'algorithm', 'optimization', 'loss function']
            math_count = sum(1 for mi in math_indicators if mi in abstract or mi in title)

            # Category encoding
            primary_category = paper.get('categories', ['unknown'])[0]

            # Author collaboration indicators
            if paper.get('authors'):
                author_initials = [len([p for p in author.split() if p]) for author in paper['authors']]
                avg_name_parts = np.mean(author_initials) if author_initials else 1
            else:
                avg_name_parts = 1

            feature_dict = {
                'paper_id': paper['paper_id'],
                'num_authors': num_authors,
                'num_categories': num_categories,
                'title_length': title_length,
                'abstract_length': abstract_length,
                'pub_year': pub_year,
                'pub_month': pub_month,
                'pub_weekday': pub_weekday,
                'keyword_count': keyword_count,
                'math_count': math_count,
                'primary_category': primary_category,
                'avg_name_parts': avg_name_parts,
                'has_multiple_categories': int(num_categories > 1),
                'is_recent': int(pub_year >= 2023)
            }

            features.append(feature_dict)

        return pd.DataFrame(features)

    def simulate_impact_scores(self, df):
        """Simulate impact scores based on realistic patterns."""

        np.random.seed(42)
        impact_scores = []

        for _, paper in df.iterrows():
            # Base score
            base_score = np.random.normal(10, 3)

            # Author count bonus (collaboration)
            if paper['num_authors'] > 5:
                base_score += 2
            elif paper['num_authors'] > 10:
                base_score += 4

            # Category bonuses
            if paper['primary_category'] in ['cs.AI', 'cs.LG']:
                base_score += 3
            elif paper['primary_category'] in ['cs.CV', 'cs.CL']:
                base_score += 2

            # Abstract length (comprehensive papers)
            if paper['abstract_length'] > 1500:
                base_score += 1.5

            # Keyword bonus
            base_score += paper['keyword_count'] * 0.5
            base_score += paper['math_count'] * 0.3

            # Recent paper penalty (too new to have citations)
            if paper['is_recent']:
                base_score *= 0.7

            # Year trend (ML has been growing)
            year_bonus = (paper['pub_year'] - 2018) * 0.2
            base_score += year_bonus

            # Add noise
            final_score = max(0, base_score + np.random.normal(0, 1))
            impact_scores.append(final_score)

        return impact_scores

    def train_model(self, df):
        """Train impact prediction model."""

        print("🤖 Training impact prediction model...")

        # Encode categorical variables
        categorical_cols = ['primary_category']

        for col in categorical_cols:
            le = LabelEncoder()
            df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
            self.label_encoders[col] = le

        # Select features for training
        feature_cols = ['num_authors', 'num_categories', 'title_length', 'abstract_length',
                       'pub_year', 'pub_month', 'pub_weekday', 'keyword_count', 'math_count',
                       'primary_category_encoded', 'avg_name_parts', 'has_multiple_categories', 'is_recent']

        X = df[feature_cols]
        y = df['impact_score']

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train model
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"✅ Model trained:")
        print(f"   R² Score: {r2:.3f}")
        print(f"   MSE: {mse:.3f}")
        print(f"   Training samples: {len(X_train)}")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        print(f"\\n📊 Top 5 Important Features:")
        for _, row in feature_importance.head().iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")

        return feature_importance

    def predict_impact(self, papers):
        """Predict impact for new papers."""

        df = self.extract_features(papers)

        # Apply same encoding as training
        for col, le in self.label_encoders.items():
            try:
                df[col + '_encoded'] = le.transform(df[col].astype(str))
            except ValueError:
                # Handle unseen categories
                df[col + '_encoded'] = 0

        feature_cols = ['num_authors', 'num_categories', 'title_length', 'abstract_length',
                       'pub_year', 'pub_month', 'pub_weekday', 'keyword_count', 'math_count',
                       'primary_category_encoded', 'avg_name_parts', 'has_multiple_categories', 'is_recent']

        X = df[feature_cols]
        predictions = self.model.predict(X)

        results = df[['paper_id']].copy()
        results['predicted_impact'] = predictions

        return results.sort_values('predicted_impact', ascending=False)

def main():
    """Main impact prediction workflow."""

    print("🎯 Starting impact prediction analysis...")

    # Load papers
    db_ops = get_operations()
    papers = list(db_ops.find_papers({
        'abstract': {'$exists': True, '$ne': ''},
        'date_published': {'$exists': True}
    }))

    if len(papers) < 100:
        print(f"❌ Need at least 100 papers for training, found {len(papers)}")
        return

    print(f"📊 Analyzing {len(papers)} papers...")

    # Initialize predictor
    predictor = ImpactPredictor()

    # Extract features
    df = predictor.extract_features(papers)

    # Simulate impact scores (in real scenario, use actual citation counts)
    df['impact_score'] = predictor.simulate_impact_scores(df)

    # Train model
    feature_importance = predictor.train_model(df)

    # Predict impact for recent papers
    recent_papers = [p for p in papers if p.get('date_published', '').startswith('2024')]

    if recent_papers:
        print(f"\\n🔮 Predicting impact for {len(recent_papers)} recent papers...")
        predictions = predictor.predict_impact(recent_papers)

        print(f"\\n🏆 Top 10 High-Impact Predictions:")
        for i, (_, row) in enumerate(predictions.head(10).iterrows(), 1):
            paper = next(p for p in recent_papers if p['paper_id'] == row['paper_id'])
            print(f"{i:2d}. {paper.get('title', '')[:80]}...")
            print(f"    Predicted Impact: {row['predicted_impact']:.2f}")
            print(f"    Authors: {len(paper.get('authors', []))} | Categories: {len(paper.get('categories', []))}")
            print(f"    arXiv: https://arxiv.org/abs/{row['paper_id']}")
            print()

        # Save predictions
        predictions_with_metadata = []
        for _, row in predictions.iterrows():
            paper = next(p for p in recent_papers if p['paper_id'] == row['paper_id'])
            predictions_with_metadata.append({
                'paper_id': row['paper_id'],
                'predicted_impact': row['predicted_impact'],
                'title': paper.get('title', ''),
                'authors': paper.get('authors', []),
                'categories': paper.get('categories', []),
                'date_published': paper.get('date_published', ''),
                'arxiv_url': f"https://arxiv.org/abs/{row['paper_id']}"
            })

        pred_df = pd.DataFrame(predictions_with_metadata)
        pred_df.to_csv('impact_predictions.csv', index=False)

        print(f"💾 Predictions saved to impact_predictions.csv")

    # Visualize feature importance
    plt.figure(figsize=(10, 6))
    sns.barplot(data=feature_importance.head(10), x='importance', y='feature')
    plt.title('Feature Importance for Impact Prediction')
    plt.tight_layout()
    plt.savefig('feature_importance.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    main()
```

---

## 🤖 Custom Agent Examples

### Example 10: Specialized Domain Agent

**Scenario**: Create a custom agent for medical AI research.

```python
#!/usr/bin/env python3
# medical_ai_agent.py

import asyncio
import re
from datetime import datetime, timedelta
from arxiv_scraper.crawler.arxiv_api import ArxivCrawler
from arxiv_scraper.database.mongodb_operations import get_operations
from arxiv_scraper.utils.logger import get_logger

class MedicalAIAgent:
    """Specialized agent for medical AI research."""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.crawler = ArxivCrawler(rate_limit_delay=3.0)
        self.db_ops = get_operations()

        # Medical AI specific keywords and patterns
        self.medical_keywords = [
            'medical imaging', 'radiology', 'pathology', 'clinical', 'healthcare',
            'medical AI', 'healthcare AI', 'diagnostic', 'medical diagnosis',
            'X-ray', 'CT scan', 'MRI', 'ultrasound', 'histology', 'biopsy',
            'electronic health records', 'EHR', 'clinical decision support',
            'drug discovery', 'pharmacology', 'medical image analysis',
            'telemedicine', 'digital health', 'precision medicine'
        ]

        self.medical_categories = [
            'cs.CV',  # Computer Vision (medical imaging)
            'cs.AI',  # AI applications in medicine
            'cs.LG',  # Machine Learning in healthcare
            'q-bio.QM',  # Quantitative Methods in Biology
            'physics.med-ph',  # Medical Physics
            'stat.AP'  # Statistics Applications (clinical trials)
        ]

        self.exclusion_keywords = [
            'theoretical', 'pure mathematics', 'abstract algebra',
            'quantum computing', 'robotics', 'autonomous'  # Unless medical
        ]

    def calculate_medical_relevance(self, paper):
        """Calculate relevance score for medical AI research."""

        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        categories = paper.get('categories', [])

        score = 0
        reasons = []

        # Keyword matching in title (higher weight)
        for keyword in self.medical_keywords:
            if keyword.lower() in title:
                score += 3
                reasons.append(f"title keyword: {keyword}")
            elif keyword.lower() in abstract:
                score += 1
                reasons.append(f"abstract keyword: {keyword}")

        # Category matching
        for category in categories:
            if category in self.medical_categories:
                score += 2
                reasons.append(f"relevant category: {category}")

        # Medical terms pattern matching
        medical_patterns = [
            r'medical\\s+(?:imaging|diagnosis|treatment)',
            r'clinical\\s+(?:trial|study|application)',
            r'patient\\s+(?:data|outcome|care)',
            r'disease\\s+(?:detection|classification|prediction)',
            r'health\\s+(?:monitoring|assessment|prediction)'
        ]

        full_text = f"{title} {abstract}"
        for pattern in medical_patterns:
            if re.search(pattern, full_text):
                score += 1.5
                reasons.append(f"medical pattern: {pattern}")

        # Penalize excluded topics
        for exclude_word in self.exclusion_keywords:
            if exclude_word in full_text:
                score -= 1
                reasons.append(f"exclusion: {exclude_word}")

        # Bonus for recent papers (medical AI is fast-moving)
        pub_date = paper.get('date_published', '')
        if pub_date:
            try:
                pub_datetime = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                days_old = (datetime.now(pub_datetime.tzinfo) - pub_datetime).days
                if days_old <= 30:
                    score += 1
                    reasons.append("recent paper bonus")
            except:
                pass

        return max(0, score), reasons

    async def collect_medical_papers(self, max_papers=200, days_back=90):
        """Collect medical AI papers."""

        self.logger.info(f"Collecting medical AI papers (last {days_back} days)")

        # Collect from medical-relevant categories
        all_papers = []

        for category in self.medical_categories:
            self.logger.info(f"Searching category: {category}")

            papers = await self.crawler.crawl_specific_categories(
                categories=[category],
                max_papers=max_papers // len(self.medical_categories),
                days_back=days_back
            )

            if papers:
                self.logger.info(f"Found {len(papers)} papers in {category}")
                all_papers.extend(papers)

        # Remove duplicates
        unique_papers = {p['paper_id']: p for p in all_papers}.values()
        unique_papers = list(unique_papers)

        self.logger.info(f"Total unique papers found: {len(unique_papers)}")

        # Score and filter for medical relevance
        medical_papers = []

        for paper in unique_papers:
            score, reasons = self.calculate_medical_relevance(paper)

            if score >= 3:  # Minimum relevance threshold
                paper['medical_relevance_score'] = score
                paper['medical_relevance_reasons'] = reasons
                paper['agent_processed'] = 'medical_ai_agent'
                paper['processed_date'] = datetime.now().isoformat()
                medical_papers.append(paper)

        # Sort by relevance
        medical_papers.sort(key=lambda x: x['medical_relevance_score'], reverse=True)

        self.logger.info(f"Selected {len(medical_papers)} medically relevant papers")

        return medical_papers

    def categorize_medical_papers(self, papers):
        """Categorize papers by medical domain."""

        categories = {
            'medical_imaging': [],
            'clinical_ai': [],
            'drug_discovery': [],
            'diagnostics': [],
            'healthcare_systems': [],
            'digital_health': [],
            'other_medical': []
        }

        categorization_rules = {
            'medical_imaging': ['imaging', 'radiology', 'x-ray', 'ct', 'mri', 'ultrasound', 'scan'],
            'clinical_ai': ['clinical', 'hospital', 'patient', 'treatment', 'therapy'],
            'drug_discovery': ['drug', 'pharmacology', 'molecule', 'compound', 'pharmaceutical'],
            'diagnostics': ['diagnosis', 'diagnostic', 'detection', 'screening', 'biomarker'],
            'healthcare_systems': ['healthcare system', 'ehr', 'electronic health', 'hospital management'],
            'digital_health': ['telemedicine', 'mobile health', 'wearable', 'remote monitoring']
        }

        for paper in papers:
            text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
            categorized = False

            for category, keywords in categorization_rules.items():
                if any(keyword in text for keyword in keywords):
                    categories[category].append(paper)
                    categorized = True
                    break

            if not categorized:
                categories['other_medical'].append(paper)

        return categories

    def generate_medical_report(self, papers):
        """Generate specialized medical AI research report."""

        categorized = self.categorize_medical_papers(papers)

        report = f"""# Medical AI Research Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total Medical AI Papers: {len(papers)}
- Average Relevance Score: {np.mean([p['medical_relevance_score'] for p in papers]):.2f}

## Papers by Medical Domain

"""

        for domain, domain_papers in categorized.items():
            if domain_papers:
                report += f"### {domain.replace('_', ' ').title()} ({len(domain_papers)} papers)\\n\\n"

                # Top 3 papers in each domain
                sorted_papers = sorted(domain_papers, key=lambda x: x['medical_relevance_score'], reverse=True)

                for i, paper in enumerate(sorted_papers[:3], 1):
                    report += f"**{i}. {paper.get('title', 'Untitled')}**\\n"
                    report += f"- Authors: {', '.join(paper.get('authors', [])[:3])}\\n"
                    report += f"- Relevance: {paper['medical_relevance_score']:.1f}\\n"
                    report += f"- Categories: {', '.join(paper.get('categories', []))}\\n"
                    report += f"- arXiv: https://arxiv.org/abs/{paper['paper_id']}\\n\\n"

        report += f"""
## Research Trends

### Most Common Medical Keywords
"""

        # Keyword frequency analysis
        all_text = ' '.join([f"{p.get('title', '')} {p.get('abstract', '')}" for p in papers])
        keyword_counts = {}

        for keyword in self.medical_keywords:
            count = all_text.lower().count(keyword.lower())
            if count > 0:
                keyword_counts[keyword] = count

        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)

        for keyword, count in sorted_keywords[:10]:
            report += f"- {keyword}: {count} mentions\\n"

        return report

    async def run_medical_analysis(self, max_papers=200, days_back=90):
        """Run complete medical AI analysis."""

        self.logger.info("Starting Medical AI Agent analysis")

        # Collect papers
        medical_papers = await self.collect_medical_papers(max_papers, days_back)

        if not medical_papers:
            self.logger.warning("No medical papers found")
            return None

        # Store in database with medical tags
        if medical_papers:
            result = self.db_ops.bulk_insert_papers(medical_papers)
            self.logger.info(f"Stored {result['inserted']} medical papers in database")

        # Generate report
        report = self.generate_medical_report(medical_papers)

        # Save report
        filename = f"medical_ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w') as f:
            f.write(report)

        self.logger.info(f"Medical AI report saved to {filename}")

        # Print summary
        print(f"\\n🏥 MEDICAL AI AGENT SUMMARY")
        print("=" * 40)
        print(f"Medical papers collected: {len(medical_papers)}")
        print(f"Average relevance score: {np.mean([p['medical_relevance_score'] for p in medical_papers]):.2f}")
        print(f"Report saved: {filename}")

        categorized = self.categorize_medical_papers(medical_papers)
        print(f"\\nDomain breakdown:")
        for domain, papers in categorized.items():
            if papers:
                print(f"  {domain.replace('_', ' ')}: {len(papers)} papers")

        return medical_papers, report

async def main():
    """Run the Medical AI Agent."""

    agent = MedicalAIAgent()
    papers, report = await agent.run_medical_analysis(max_papers=300, days_back=60)

if __name__ == "__main__":
    import numpy as np  # For mean calculation
    asyncio.run(main())
```

---

## 🎯 Usage Tips for Examples

### Quick Testing

```bash
# Test any Python example with small datasets first
python example_script.py --max-papers 10 --log-level DEBUG
```

### Modify for Your Research

1. **Update keywords**: Change search terms in the examples
2. **Adjust time ranges**: Modify `days_back` parameters
3. **Customize categories**: Update arXiv category lists
4. **Set email alerts**: Configure SMTP settings in monitoring examples

### Performance Optimization

```bash
# For large datasets, use these patterns:
# 1. Process in batches
# 2. Save intermediate results
# 3. Use async operations where available
# 4. Monitor memory usage
```

### Integration with Other Tools

- **Jupyter Notebooks**: Copy code blocks into notebook cells
- **Cron Jobs**: Use automation examples for scheduled runs
- **Web Apps**: Adapt analysis code for Flask/Django apps
- **APIs**: Wrap functionality in REST endpoints

---

*For more examples and use cases, check [WORKFLOWS.md](WORKFLOWS.md) and [FAQ.md](FAQ.md).*
