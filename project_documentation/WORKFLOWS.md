# Research Workflows Guide

**Common research scenarios with step-by-step instructions**

This guide shows you how to accomplish specific research tasks using the arXiv Paper Scraper.

## 📚 Table of Contents

- [Literature Review Workflows](#-literature-review-workflows)
- [Research Area Exploration](#-research-area-exploration)
- [Trend Analysis Workflows](#-trend-analysis-workflows)
- [Collaboration & Citation Workflows](#-collaboration--citation-workflows)
- [Data Export Workflows](#-data-export-workflows)
- [Automated Monitoring Workflows](#-automated-monitoring-workflows)

---

## 📖 Literature Review Workflows

### Scenario 1: "I need papers on transformers for my thesis"

**Goal**: Collect comprehensive set of transformer-related papers

```bash
# Step 1: Broad transformer search (last 2 years)
python main.py \
  --keywords "transformer,attention,bert,gpt" \
  --max-papers 200 \
  --days-back 730 \
  --download-pdfs \
  --log-level INFO

# Step 2: Specific architecture papers
python main.py \
  --keywords "transformer architecture,multi-head attention" \
  --categories "cs.CL,cs.LG" \
  --max-papers 100 \
  --days-back 1095 \
  --download-pdfs

# Step 3: Recent developments (last 3 months)
python main.py \
  --keywords "transformer,attention" \
  --max-papers 150 \
  --days-back 90 \
  --download-pdfs
```

**Expected outcome:**
- ✅ 400+ transformer papers in database
- ✅ PDFs organized by date in `papers/arxiv/`
- ✅ Comprehensive coverage from foundational to recent papers

**Next steps:**
```bash
# Export for analysis
python -c "
from arxiv_scraper.database.mongodb_operations import get_operations
db_ops = get_operations()
papers = db_ops.search_papers_by_keyword('transformer')
print(f'Found {len(list(papers))} transformer papers')
"
```

### Scenario 2: "I need to survey computer vision methods"

**Goal**: Systematic survey of CV techniques

```bash
# Step 1: Core CV categories
python main.py \
  --categories "cs.CV" \
  --max-papers 500 \
  --days-back 365 \
  --download-pdfs

# Step 2: Specific CV topics
python main.py \
  --keywords "object detection,semantic segmentation,image classification" \
  --categories "cs.CV,cs.LG" \
  --max-papers 300 \
  --days-back 730 \
  --download-pdfs

# Step 3: Recent breakthrough papers
python main.py \
  --keywords "vision transformer,diffusion model,stable diffusion" \
  --max-papers 200 \
  --days-back 180 \
  --download-pdfs
```

**Quality check:**
```bash
# Verify coverage
python -c "
import pymongo
client = pymongo.MongoClient()
db = client.arxiv_scraper
cv_papers = db.papers.count_documents({'categories': {'$in': ['cs.CV']}})
print(f'Computer Vision papers: {cv_papers}')
all_papers = db.papers.count_documents({})
print(f'Total papers: {all_papers}')
print(f'CV coverage: {cv_papers/all_papers*100:.1f}%')
"
```

---

## 🔍 Research Area Exploration

### Scenario 3: "What's new in AI safety?"

**Goal**: Explore emerging AI safety research

```bash
# Step 1: AI safety keywords search
python main.py \
  --keywords "AI safety,alignment,interpretability,explainable AI" \
  --max-papers 150 \
  --days-back 365 \
  --download-pdfs \
  --log-level DEBUG

# Step 2: Broader safety-related topics
python main.py \
  --keywords "robustness,fairness,bias,ethics" \
  --categories "cs.AI,cs.LG,cs.CY" \
  --max-papers 200 \
  --days-back 365 \
  --download-pdfs

# Step 3: Recent safety papers only
python main.py \
  --keywords "AI safety,alignment" \
  --max-papers 100 \
  --days-back 90 \
  --download-pdfs
```

**Analysis workflow:**
```bash
# Create analysis dataset
python -c "
import pandas as pd
from arxiv_scraper.database.mongodb_operations import get_operations

db_ops = get_operations()
safety_papers = list(db_ops.search_papers_by_keyword('safety'))

df = pd.DataFrame(safety_papers)
if len(df) > 0:
    df['date_published'] = pd.to_datetime(df['date_published'])
    df['month'] = df['date_published'].dt.to_period('M')
    
    monthly_counts = df.groupby('month').size()
    print('AI Safety Papers Per Month:')
    print(monthly_counts.tail(12))  # Last 12 months
    
    df.to_csv('ai_safety_papers.csv', index=False)
    print(f'Exported {len(df)} safety papers to ai_safety_papers.csv')
else:
    print('No safety papers found. Try broadening search terms.')
"
```

### Scenario 4: "Find interdisciplinary ML applications"

**Goal**: Discover ML applications across different domains

```bash
# Step 1: ML in different sciences
python main.py \
  --keywords "machine learning,deep learning" \
  --categories "physics.comp-ph,q-bio.QM,stat.ML" \
  --max-papers 200 \
  --days-back 365 \
  --download-pdfs

# Step 2: Applied ML in specific domains
python main.py \
  --keywords "medical AI,financial ML,climate modeling" \
  --max-papers 150 \
  --days-back 365 \
  --download-pdfs

# Step 3: Recent interdisciplinary work
python main.py \
  --keywords "ML application,deep learning application" \
  --max-papers 100 \
  --days-back 180 \
  --download-pdfs
```

**Domain analysis:**
```bash
# Analyze by category distribution
python -c "
from collections import Counter
from arxiv_scraper.database.mongodb_operations import get_operations

db_ops = get_operations()
papers = list(db_ops.find_papers({}))

all_categories = []
for paper in papers:
    all_categories.extend(paper.get('categories', []))

category_counts = Counter(all_categories)
print('Top 15 Categories:')
for cat, count in category_counts.most_common(15):
    print(f'{cat}: {count} papers')
"
```

---

## 📊 Trend Analysis Workflows

### Scenario 5: "Track the evolution of deep learning"

**Goal**: Analyze how deep learning research has evolved

```bash
# Step 1: Collect historical deep learning papers (last 3 years)
python main.py \
  --keywords "deep learning,neural network" \
  --categories "cs.LG,cs.AI,cs.NE" \
  --max-papers 1000 \
  --days-back 1095 \
  --download-pdfs

# Step 2: Specific deep learning architectures
python main.py \
  --keywords "CNN,RNN,LSTM,GAN,transformer,diffusion" \
  --max-papers 500 \
  --days-back 1095 \
  --download-pdfs

# Step 3: Recent trends (last 6 months)
python main.py \
  --keywords "large language model,foundation model,multimodal" \
  --max-papers 300 \
  --days-back 180 \
  --download-pdfs
```

**Trend analysis script:**
```bash
# Create trend analysis
python -c "
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from arxiv_scraper.database.mongodb_operations import get_operations

db_ops = get_operations()
papers = list(db_ops.find_papers({}))

df = pd.DataFrame(papers)
df['date_published'] = pd.to_datetime(df['date_published'])
df['year_month'] = df['date_published'].dt.to_period('M')

# Keywords to track
keywords = ['transformer', 'CNN', 'GAN', 'LSTM', 'diffusion']
trends = {}

for keyword in keywords:
    keyword_papers = df[df['abstract'].str.contains(keyword, case=False, na=False)]
    monthly_counts = keyword_papers.groupby('year_month').size()
    trends[keyword] = monthly_counts

# Plot trends
plt.figure(figsize=(12, 8))
for keyword, counts in trends.items():
    if len(counts) > 0:
        plt.plot(counts.index.astype(str), counts.values, marker='o', label=keyword)

plt.title('Deep Learning Architecture Trends Over Time')
plt.xlabel('Month')
plt.ylabel('Number of Papers')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('dl_trends.png', dpi=150)
plt.show()

print('Trend analysis saved as dl_trends.png')
"
```

### Scenario 6: "Monitor new research areas"

**Goal**: Set up automated monitoring for emerging topics

```bash
# Step 1: Monitor recent papers daily
# Create monitoring script
cat > monitor_new_papers.sh << 'EOF'
#!/bin/bash
echo "$(date): Checking for new papers..."

python main.py \
  --days-back 1 \
  --max-papers 50 \
  --download-pdfs \
  --log-level INFO \
  --log-file "daily_monitor_$(date +%Y%m%d).log"

# Check for specific emerging topics
python main.py \
  --keywords "quantum machine learning,federated learning,neuromorphic" \
  --days-back 7 \
  --max-papers 20 \
  --download-pdfs

echo "$(date): Monitoring complete"
EOF

chmod +x monitor_new_papers.sh
```

**Run monitoring:**
```bash
# Manual check
./monitor_new_papers.sh

# Setup daily monitoring (optional)
# Add to crontab: 0 9 * * * /path/to/monitor_new_papers.sh
```

---

## 👥 Collaboration & Citation Workflows

### Scenario 7: "Find papers by specific research groups"

**Goal**: Track output from leading AI research labs

```bash
# Step 1: Papers from major AI labs (by common author affiliations)
python main.py \
  --keywords "OpenAI,DeepMind,Google Brain,Meta AI,Stanford,MIT" \
  --max-papers 300 \
  --days-back 365 \
  --download-pdfs

# Step 2: Papers by influential authors (requires manual keyword refinement)
python main.py \
  --keywords "Geoffrey Hinton,Yann LeCun,Andrew Ng,Fei-Fei Li" \
  --max-papers 100 \
  --days-back 730 \
  --download-pdfs
```

**Author analysis:**
```bash
# Analyze most prolific authors
python -c "
from collections import Counter
from arxiv_scraper.database.mongodb_operations import get_operations

db_ops = get_operations()
papers = list(db_ops.find_papers({}))

all_authors = []
for paper in papers:
    all_authors.extend(paper.get('authors', []))

author_counts = Counter(all_authors)
print('Most Prolific Authors:')
for author, count in author_counts.most_common(20):
    print(f'{author}: {count} papers')
"
```

### Scenario 8: "Build collaboration network"

**Goal**: Map research collaborations

```bash
# Collect comprehensive dataset for network analysis
python main.py \
  --categories "cs.AI,cs.LG,cs.CV,cs.CL" \
  --max-papers 1000 \
  --days-back 365 \
  --download-pdfs
```

**Network analysis:**
```bash
# Create collaboration network
python -c "
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
from arxiv_scraper.database.mongodb_operations import get_operations

db_ops = get_operations()
papers = list(db_ops.find_papers({}))

# Build collaboration graph
G = nx.Graph()

for paper in papers:
    authors = paper.get('authors', [])
    if len(authors) > 1:
        # Add edges between all co-authors
        for author1, author2 in combinations(authors, 2):
            if G.has_edge(author1, author2):
                G[author1][author2]['weight'] += 1
            else:
                G.add_edge(author1, author2, weight=1)

# Find most connected researchers
centrality = nx.degree_centrality(G)
top_researchers = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]

print('Most Connected Researchers:')
for researcher, centrality_score in top_researchers:
    print(f'{researcher}: {centrality_score:.3f}')

print(f'\\nNetwork Stats:')
print(f'Authors: {G.number_of_nodes()}')
print(f'Collaborations: {G.number_of_edges()}')
"
```

---

## 💾 Data Export Workflows

### Scenario 9: "Export data for machine learning analysis"

**Goal**: Prepare clean datasets for ML research

```bash
# Step 1: Collect comprehensive ML dataset
python main.py \
  --categories "cs.LG,cs.AI,stat.ML" \
  --max-papers 2000 \
  --days-back 730 \
  --download-pdfs
```

**Export for different ML tasks:**
```bash
# Create ML-ready datasets
python -c "
import pandas as pd
import json
from sklearn.model_selection import train_test_split
from arxiv_scraper.database.mongodb_operations import get_operations

db_ops = get_operations()
papers = list(db_ops.find_papers({
    'abstract': {'$exists': True, '$ne': ''},
    'categories': {'$exists': True}
}))

df = pd.DataFrame(papers)

# Text classification dataset
classification_data = []
for _, paper in df.iterrows():
    for category in paper['categories']:
        classification_data.append({
            'text': paper['title'] + ' ' + paper['abstract'],
            'label': category,
            'paper_id': paper['paper_id']
        })

class_df = pd.DataFrame(classification_data)

# Split dataset
train_df, test_df = train_test_split(class_df, test_size=0.2, random_state=42)

# Export datasets
train_df.to_csv('arxiv_classification_train.csv', index=False)
test_df.to_csv('arxiv_classification_test.csv', index=False)

# Summary statistics dataset
summary_data = {
    'total_papers': len(df),
    'date_range': {
        'earliest': df['date_published'].min(),
        'latest': df['date_published'].max()
    },
    'categories': df['categories'].explode().value_counts().to_dict(),
    'avg_abstract_length': df['abstract'].str.len().mean()
}

with open('dataset_summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2, default=str)

print(f'Exported:')
print(f'- Training set: {len(train_df)} samples')
print(f'- Test set: {len(test_df)} samples')
print(f'- Summary: dataset_summary.json')
"
```

### Scenario 10: "Create research bibliography"

**Goal**: Generate formatted citations for papers

```bash
# Collect papers for bibliography
python main.py \
  --keywords "your_research_topic" \
  --max-papers 100 \
  --days-back 365 \
  --download-pdfs
```

**Generate bibliography:**
```bash
# Create BibTeX format bibliography
python -c "
from arxiv_scraper.database.mongodb_operations import get_operations

db_ops = get_operations()
papers = list(db_ops.find_papers({}))

def to_bibtex(paper):
    authors = ' and '.join(paper.get('authors', ['Unknown']))
    title = paper.get('title', 'Untitled')
    year = paper.get('date_published', '')[:4] if paper.get('date_published') else 'Unknown'
    
    bibtex = f'''@article{{{paper['paper_id']},
    author = {{{authors}}},
    title = {{{title}}},
    year = {{{year}}},
    eprint = {{{paper['paper_id']}}},
    archivePrefix = {{arXiv}},
    primaryClass = {{{paper.get('categories', [''])[0] if paper.get('categories') else ''}}}
}}'''
    return bibtex

with open('bibliography.bib', 'w') as f:
    for paper in papers[:50]:  # Limit to 50 papers
        f.write(to_bibtex(paper) + '\\n\\n')

print('Bibliography saved to bibliography.bib')
"
```

---

## ⚙️ Automated Monitoring Workflows

### Scenario 11: "Daily research alerts"

**Goal**: Get daily alerts about new papers in your field

**Setup automated daily monitoring:**

```bash
# Create daily monitoring script
cat > daily_research_alerts.py << 'EOF'
#!/usr/bin/env python3
import sys
import asyncio
from datetime import datetime
from arxiv_scraper.crawler.arxiv_api import ArxivCrawler
from arxiv_scraper.database.mongodb_operations import get_operations

async def daily_alerts():
    # Your research interests
    keywords = ["your_research_keywords_here"]  # Customize this
    categories = ["cs.AI", "cs.LG"]  # Customize this
    
    crawler = ArxivCrawler()
    db_ops = get_operations()
    
    # Get yesterday's papers
    papers = await crawler.crawl_specific_categories(
        categories=categories,
        max_papers=50,
        days_back=1
    )
    
    # Filter by your keywords
    relevant_papers = []
    for paper in papers:
        abstract_lower = paper.get('abstract', '').lower()
        if any(keyword.lower() in abstract_lower for keyword in keywords):
            relevant_papers.append(paper)
    
    if relevant_papers:
        print(f"\\n🔔 {len(relevant_papers)} new relevant papers found!")
        print("=" * 50)
        
        for paper in relevant_papers:
            print(f"Title: {paper['title']}")
            print(f"Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
            print(f"Categories: {', '.join(paper['categories'])}")
            print(f"URL: https://arxiv.org/abs/{paper['paper_id']}")
            print("-" * 30)
    else:
        print("No new relevant papers today.")

if __name__ == "__main__":
    asyncio.run(daily_alerts())
EOF

chmod +x daily_research_alerts.py
```

**Test and schedule:**
```bash
# Test the alert system
python daily_research_alerts.py

# Schedule daily alerts (add to crontab)
# crontab -e
# Add line: 0 9 * * * cd /path/to/arxiv_scraper && python daily_research_alerts.py > daily_alerts.log 2>&1
```

### Scenario 12: "Weekly research digest"

**Goal**: Weekly summary of research activity

```bash
# Create weekly digest script
cat > weekly_digest.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
from datetime import datetime, timedelta
from arxiv_scraper.database.mongodb_operations import get_operations

def generate_weekly_digest():
    db_ops = get_operations()
    
    # Get papers from last 7 days
    week_ago = datetime.now() - timedelta(days=7)
    recent_papers = list(db_ops.find_papers({
        'date_scraped': {'$gte': week_ago.isoformat()}
    }))
    
    if not recent_papers:
        print("No papers collected this week.")
        return
    
    df = pd.DataFrame(recent_papers)
    
    print(f"\\n📊 WEEKLY RESEARCH DIGEST")
    print(f"{'=' * 40}")
    print(f"Period: {week_ago.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Total papers: {len(df)}")
    
    # Top categories
    all_categories = []
    for categories in df['categories']:
        all_categories.extend(categories)
    
    category_counts = pd.Series(all_categories).value_counts()
    print(f"\\n🏷️  Top Categories:")
    for cat, count in category_counts.head(10).items():
        print(f"   {cat}: {count} papers")
    
    # Papers with most downloads (if tracking downloads)
    if 'pdf_downloaded' in df.columns:
        downloaded = df[df['pdf_downloaded'] == True]
        print(f"\\n📥 Downloads: {len(downloaded)}/{len(df)} papers")
    
    print(f"\\n🔗 Recent highlights:")
    for _, paper in df.head(5).iterrows():
        print(f"   • {paper['title'][:80]}...")

if __name__ == "__main__":
    generate_weekly_digest()
EOF

chmod +x weekly_digest.py
```

**Schedule weekly digest:**
```bash
# Test weekly digest
python weekly_digest.py

# Schedule weekly (add to crontab)
# 0 9 * * 1 cd /path/to/arxiv_scraper && python weekly_digest.py > weekly_digest.log 2>&1
```

---

## 🎯 Workflow Tips

### Best Practices:
- **Start small**: Test with `--max-papers 10` before large runs
- **Use rate limiting**: Respect arXiv with `--rate-limit 3.0` minimum
- **Monitor storage**: Check `du -sh papers/` regularly
- **Log everything**: Use `--log-file` for debugging
- **Backup data**: Export database regularly

### Common Issues:
- **Rate limiting**: If you get 429 errors, increase `--rate-limit`
- **Storage full**: Clean old papers or increase `--max-storage`
- **No results**: Try broader keywords or longer `--days-back`
- **Slow downloads**: Reduce `--max-concurrent` downloads

### Performance Optimization:
```bash
# Fast metadata-only collection
python main.py --max-papers 500 --days-back 30  # No --download-pdfs

# Efficient batch processing
python main.py --max-papers 100 --download-pdfs --max-concurrent 3

# Storage-conscious collection
python main.py --max-papers 50 --max-storage 50  # Limit storage to 50GB
```

---

*Need more specific help? Check [EXAMPLES.md](EXAMPLES.md) for code examples or [FAQ.md](FAQ.md) for troubleshooting.*