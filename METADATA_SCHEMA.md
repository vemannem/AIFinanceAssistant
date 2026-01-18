# Pinecone Metadata Schema Documentation

**Status:** Phase 1 Implementation Complete ✅  
**Date:** January 13, 2026  
**Reference:** Complete metadata specification for RAG vector database

---

## Complete Metadata Schema

### Vector Structure in Pinecone

Every vector stored in the `ai-finance-knowledge-base` index contains:

```python
{
  "id": "chunk_id_abc123",                    # Unique chunk identifier
  "values": [1536-dimensional vector],        # OpenAI text-embedding-3-small embedding
  "metadata": {
    "article_id": "art_001",                  # Unique identifier for source article
    "article_title": "Understanding ETFs",    # Full title of financial article
    "category": "etfs",                       # Finance category
    "source_url": "https://investopedia.com/terms/e/etf.asp",  # Source URL
    "publish_date": "2023-06-15",             # Publication date
    "source": "investopedia",                 # Source domain
    "chunk_index": 0,                         # Sequential chunk position
    "token_count": 512                        # Token count in chunk
  }
}
```

---

## Metadata Fields Reference (8 Required Fields)

### Field Specifications

| Field | Type | Purpose | Source | Example | Used For |
|-------|------|---------|--------|---------|----------|
| `article_id` | str | Unique identifier for source article | download_articles.py | "art_001" | Grouping chunks, tracking lineage |
| `article_title` | str | Full title of financial article | download_articles.py | "What is an ETF and How to Invest?" | Citations, display to users |
| `category` | str | Finance topic/category | download_articles.py | "etfs", "portfolio", "tax", "bonds" | Filtering results, intent routing |
| `source_url` | str | Clickable link to original source | download_articles.py | "https://investopedia.com/..." | Citations, attribution, user reference |
| `publish_date` | str | ISO 8601 publication date | download_articles.py | "2023-06-15" | Freshness checking, sorting |
| `source` | str | Source domain/publication name | download_articles.py | "investopedia", "yahoofiance", "sec" | Attribution, filtering by source |
| `chunk_index` | int | Sequential position in article (0-indexed) | chunk_articles.py | 0, 1, 2, 3... | Reconstruction, ordering |
| `token_count` | int | Actual tokens in this chunk | chunk_articles.py | 512, 489, 501 | Quality metrics, size distribution |

---

## Data Population Pipeline

### Step 1: Download Articles
**File:** `src/data/scripts/download_articles.py`

Extracts from web scraping:
- `article_id` - Generated UUID
- `article_title` - From page `<title>` or heading
- `source_url` - Full HTTP URL
- `source` - Extracted domain (investopedia, yahoofiance)
- `publish_date` - From article metadata or current date
- `category` - Manually tagged or extracted from URL
- `content` - Raw article text

**Output:** `src/data/processed_articles/financial_articles_raw.json` (25 articles)

```json
{
  "article_id": "art_001",
  "article_title": "ETFs: What They Are and How to Invest",
  "source_url": "https://www.investopedia.com/terms/e/etf.asp",
  "source": "investopedia",
  "publish_date": "2023-06-15",
  "category": "etfs",
  "content": "An exchange-traded fund (ETF) is..."
}
```

### Step 2: Chunk Articles
**File:** `src/data/scripts/chunk_articles.py`

Creates semantic chunks and preserves/adds:
- `chunk_id` - Unique identifier for chunk
- `chunk_index` - Position in article
- `token_count` - Actual token count using tiktoken
- All original fields from article

**Output:** `src/data/processed_articles/articles_chunked.json` (34 chunks)

```json
{
  "chunk_id": "chunk_001",
  "article_id": "art_001",
  "article_title": "ETFs: What They Are and How to Invest",
  "source_url": "https://www.investopedia.com/terms/e/etf.asp",
  "source": "investopedia",
  "publish_date": "2023-06-15",
  "category": "etfs",
  "chunk_index": 0,
  "token_count": 512,
  "content": "An exchange-traded fund (ETF) is a type of investment fund..."
}
```

### Step 3: Ingest to Pinecone
**File:** `src/data/scripts/ingest_pinecone.py`

Embeds chunks and uploads with full metadata:
- Embeds `content` field → 1536-dimensional vector
- Creates vector metadata dict from all fields EXCEPT `content`
- Uploads to Pinecone index

**Code Reference:**
```python
for chunk, embedding in zip(batch, embeddings):
    vector = {
        "id": chunk['chunk_id'],
        "values": embedding,  # 1536-dim OpenAI embedding
        "metadata": {
            "article_id": chunk['article_id'],
            "article_title": chunk['article_title'],
            "category": chunk['category'],
            "source_url": chunk['source_url'],
            "publish_date": chunk['publish_date'],
            "source": chunk['source'],
            "chunk_index": chunk['chunk_index'],
            "token_count": chunk['token_count']
        }
    }
    vectors.append(vector)
```

**Pinecone Index Name:** `ai-finance-knowledge-base`  
**Total Vectors:** 34 (Phase 1)  
**Dimension:** 1536  
**Metric:** cosine similarity  

---

## How Metadata is Used

### 1. Query Retrieval (RAG Pipeline)

**File:** `src/rag/__init__.py`

```
User Query
  ↓
Embed query with text-embedding-3-small
  ↓
Search Pinecone (cosine similarity)
  ↓
Retrieve top-K matches with metadata
  ↓
Filter by MIN_RELEVANCE_THRESHOLD (0.50)
  ↓
Return: [chunk_text, metadata, match_score]
```

### 2. Citation Generation

**File:** `src/web_app/routes/chat.py`

```python
# Extract metadata from retrieved chunks
citations = [
    {
        "title": match.metadata["article_title"],
        "source_url": match.metadata["source_url"],
        "category": match.metadata["category"]
    }
    for match in matches
]
```

**User Response:**
```json
{
  "message": "An ETF is...",
  "citations": [
    {
      "title": "Exchange-Traded Fund (ETF): What It Is and How to Invest",
      "source_url": "https://investopedia.com/terms/e/etf.asp",
      "category": "etfs"
    }
  ]
}
```

### 3. Filtering by Category

**Usage:** Optional `category_filter` in chat requests

```python
# In RAG retriever
if category_filter:
    results = index.query(
        vector=query_embedding,
        top_k=5,
        filter={"category": {"$eq": category_filter}}  # Filter by metadata
    )
```

### 4. Metadata Tracking

**Agent Output Metadata:**
```python
metadata = {
    "chunks_retrieved": 3,
    "tools_used": ["pinecone_retrieval", "openai_chat"],
    "top_score": 0.68,
    "categories": ["etfs", "portfolio"]
}
```

---

## Pinecone Index Configuration

### YAML Schema
```yaml
index_name: "ai-finance-knowledge-base"
dimension: 1536  # OpenAI text-embedding-3-small output
metric: "cosine"  # Cosine similarity for text embeddings
serverless:
  cloud: "aws"
  region: "us-east-1"
pod_type: null  # Serverless (no pod selection)
metadata_fields:
  - name: "article_id"
    type: "string"
  - name: "article_title"
    type: "string"
  - name: "category"
    type: "string"
  - name: "source_url"
    type: "string"
  - name: "publish_date"
    type: "string"
  - name: "source"
    type: "string"
  - name: "chunk_index"
    type: "integer"
  - name: "token_count"
    type: "integer"
```

---

## Phase 1 Data Status

### Articles Ingested: 25
- **Investopedia:** 20 articles
- **Yahoo Finance:** 5 articles

### Chunks Created: 34
- **Total Vectors:** 34 (one vector per chunk)
- **Avg Chunk Size:** ~512 tokens
- **Token Overlap:** 50 tokens between chunks
- **Metadata Completeness:** 100% (8/8 fields populated per vector)

### Example Data Points
```
Article 1: "ETFs: What They Are and How to Invest"
  → Chunk 0 (512 tokens): article_id=art_001, chunk_index=0, category=etfs
  → Chunk 1 (489 tokens): article_id=art_001, chunk_index=1, category=etfs

Article 2: "Asset Allocation: What It Is and Why It Matters"
  → Chunk 0 (512 tokens): article_id=art_002, chunk_index=0, category=portfolio
  → Chunk 1 (501 tokens): article_id=art_002, chunk_index=1, category=portfolio
  
... (34 total chunks across 25 articles)
```

---

## Production Considerations

### 1. Storage
- **What's NOT stored in metadata:** Chunk content (to save space)
- **Why:** Metadata-only storage is more efficient in Pinecone
- **Production alternative:** Store chunks in separate database, retrieve by chunk_id

### 2. Searching Across Chunks
- Same article chunks can be retrieved in same query
- `article_id` allows grouping/deduplication if needed
- `chunk_index` enables reconstruction in order

### 3. Freshness
- `publish_date` can be used for sorting by recency
- Consider implementing automatic purging of old articles
- Example: "Show only articles from last 6 months"

### 4. Multi-Source Attribution
- `source` field distinguishes between sources
- Frontend can render different badges (Investopedia vs Yahoo vs SEC)
- Enables transparent source tracking

### 5. Category-Based Routing
- Future: Intent router uses `category` to filter relevant documents
- Example: Tax question → filter to tax-related articles only
- Reduces hallucination from off-topic documents

---

## Example RAG Flow with Metadata

```
User: "What is an ETF?"

1. EMBEDDING
   Query embedding: [0.123, -0.456, 0.789, ... ] (1536 dims)

2. PINECONE SEARCH
   Query vector against 34 vectors in index
   Top matches by cosine similarity:
   
   Match 1: chunk_001
   - Score: 0.68
   - Metadata:
     {
       "article_id": "art_001",
       "article_title": "Exchange-Traded Fund (ETF): What It Is and How to Invest",
       "category": "etfs",
       "source_url": "https://investopedia.com/terms/e/etf.asp",
       "publish_date": "2023-06-15",
       "source": "investopedia",
       "chunk_index": 0,
       "token_count": 512
     }
   
   Match 2: chunk_003
   - Score: 0.62
   - Metadata: (similar structure)

3. CITATION GENERATION
   Extract from Match 1 metadata:
   Citation = {
     "title": "Exchange-Traded Fund (ETF): What It Is and How to Invest",
     "source_url": "https://investopedia.com/terms/e/etf.asp",
     "category": "etfs"
   }

4. API RESPONSE
   {
     "message": "An ETF is an investment fund traded on stock exchanges...",
     "citations": [
       {
         "title": "Exchange-Traded Fund (ETF): What It Is and How to Invest",
         "source_url": "https://investopedia.com/terms/e/etf.asp",
         "category": "etfs"
       }
     ]
   }
```

---

## Key Takeaways

✅ **8 metadata fields** stored per vector (article_id, title, category, URL, date, source, chunk_index, token_count)

✅ **Complete traceability** from raw article → chunk → vector → citation

✅ **Filtering & attribution** enabled by rich metadata

✅ **No content in metadata** - keeps Pinecone lean and fast

✅ **Production-ready** schema designed for scaling to 1000+ articles

---

**Last Updated:** January 13, 2026  
**Next Update:** When adding more articles or metadata fields  
**Maintained By:** Backend team
