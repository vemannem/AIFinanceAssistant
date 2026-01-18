#!/usr/bin/env python3
"""Pinecone Ingester - Embeds articles and uploads to Pinecone vector database."""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
import openai
from pinecone import Pinecone, ServerlessSpec

# Load environment variables from .env
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parent.parent / "processed_articles"

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME", "ai-finance-knowledge-base")
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


def validate_keys():
    """Validate required API keys."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment")
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not set in environment")
    logger.info("✅ API keys validated")


def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Embed a batch of texts using OpenAI.
    Returns: List of embedding vectors.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        encoding_format="float"
    )
    
    embeddings = [item.embedding for item in response.data]
    return embeddings


def prepare_vectors(chunks: List[Dict]) -> List[Dict]:
    """
    Prepare vectors for Pinecone upsert.
    Input: List of chunk dicts with 'content' field
    Output: List of dicts with id, values (embedding), and metadata
    """
    logger.info(f"📊 Preparing {len(chunks)} chunks for embedding...")
    
    vectors = []
    
    # Batch embed
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c['content'] for c in batch]
        
        logger.info(f"  Embedding batch {i // BATCH_SIZE + 1} ({len(batch)} chunks)...")
        embeddings = embed_batch(texts)
        
        for chunk, embedding in zip(batch, embeddings):
            vector = {
                "id": chunk['chunk_id'],
                "values": embedding,
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
    
    logger.info(f"✅ Prepared {len(vectors)} vectors")
    return vectors


def upsert_to_pinecone(vectors: List[Dict]):
    """
    Upsert vectors to Pinecone index.
    """
    logger.info(f"🔗 Connecting to Pinecone ({PINECONE_INDEX})...")
    
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    
    logger.info(f"📤 Upserting {len(vectors)} vectors...")
    
    # Upsert in batches
    for i in range(0, len(vectors), BATCH_SIZE):
        batch = vectors[i:i + BATCH_SIZE]
        index.upsert(vectors=batch)
        logger.info(f"  ✓ Batch {i // BATCH_SIZE + 1} uploaded ({len(batch)} vectors)")
    
    logger.info(f"✅ Upsert complete")


def verify_index(vectors: List[Dict]):
    """Verify index stats."""
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    
    stats = index.describe_index_stats()
    logger.info(f"📊 Index stats: {stats}")
    
    print(f"\n🎉 Pinecone Ingestion Complete!")
    print(f"  Index: {PINECONE_INDEX}")
    print(f"  Vectors uploaded: {len(vectors)}")
    print(f"  Dimension: 1536")
    print(f"  Metric: cosine\n")


def main():
    """Main execution."""
    print("\n⚡ Pinecone Ingester (Embedding + Upload)\n")
    
    validate_keys()
    
    # Load chunks
    chunks_file = PROCESSED_DIR / "articles_chunked.json"
    if not chunks_file.exists():
        logger.error(f"Chunked articles not found: {chunks_file}")
        logger.info("Run chunk_articles.py first")
        return
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    logger.info(f"📚 Loaded {len(chunks)} chunks from {chunks_file}")
    
    # Embed and prepare vectors
    vectors = prepare_vectors(chunks)
    
    # Upsert to Pinecone
    upsert_to_pinecone(vectors)
    
    # Verify
    verify_index(vectors)
    
    print(f"✅ RAG pipeline ready for queries!\n")


if __name__ == "__main__":
    main()
