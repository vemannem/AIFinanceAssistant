#!/usr/bin/env python3
"""Article Chunker - Splits articles into semantic chunks with token-level control."""

import json
import logging
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict

import tiktoken

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parent.parent / "raw_articles"
PROCESSED_DIR = Path(__file__).parent.parent / "processed_articles"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Target chunk size in tokens
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Use GPT-3.5 tokenizer (compatible with embeddings model)
tokenizer = tiktoken.get_encoding("cl100k_base")


@dataclass
class ArticleChunk:
    """Represents a chunk of an article."""
    chunk_id: str
    article_id: str
    article_title: str
    content: str
    token_count: int
    chunk_index: int
    category: str
    source_url: str
    publish_date: str
    source: str


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(tokenizer.encode(text))


def chunk_text_by_sentences(text: str, target_tokens: int = CHUNK_SIZE, overlap_tokens: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into chunks by sentences, respecting token limits.
    Maintains overlap between chunks for context preservation.
    """
    sentences = text.split('. ')
    if not sentences[-1].endswith('.'):
        sentences[-1] += '.'
    else:
        # Re-attach periods that were removed
        sentences = [s if s.endswith('.') else s + '.' for s in sentences]

    chunks = []
    current_chunk = ""
    overlap_buffer = ""

    for sentence in sentences:
        test_chunk = current_chunk + sentence + " "
        token_count = count_tokens(test_chunk)

        if token_count > target_tokens and current_chunk:
            # Save current chunk and start new one
            chunks.append(current_chunk.strip())
            
            # Build overlap: take last N tokens from current chunk
            overlap_tokens_list = tokenizer.encode(current_chunk)[-overlap_tokens:] if overlap_tokens > 0 else []
            overlap_buffer = tokenizer.decode(overlap_tokens_list)
            
            current_chunk = overlap_buffer + " " + sentence + " "
        else:
            current_chunk = test_chunk

    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def chunk_articles(raw_file: str = "financial_articles_raw.json") -> List[ArticleChunk]:
    """
    Load articles and chunk them.
    Returns: List of ArticleChunk objects.
    """
    raw_path = RAW_DIR / raw_file
    
    if not raw_path.exists():
        logger.error(f"Raw articles file not found: {raw_path}")
        return []

    with open(raw_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    logger.info(f"📚 Chunking {len(articles)} articles...")
    
    chunks = []
    total_chunks = 0

    for article in articles:
        article_id = article.get('id', f"article_{len(chunks)}")
        title = article.get('title', 'Untitled')
        content = article.get('content', '')
        category = article.get('category', 'general')
        source_url = article.get('url', '')
        publish_date = article.get('publish_date', '')
        source = article.get('source', 'unknown')

        # Skip short articles
        if count_tokens(content) < 50:
            logger.warning(f"⚠️ Skipping {title[:30]} (too short)")
            continue

        # Chunk the article
        article_chunks = chunk_text_by_sentences(content, CHUNK_SIZE, CHUNK_OVERLAP)

        for chunk_idx, chunk_text in enumerate(article_chunks):
            chunk = ArticleChunk(
                chunk_id=f"{article_id}_chunk_{chunk_idx}",
                article_id=article_id,
                article_title=title,
                content=chunk_text,
                token_count=count_tokens(chunk_text),
                chunk_index=chunk_idx,
                category=category,
                source_url=source_url,
                publish_date=publish_date,
                source=source
            )
            chunks.append(chunk)
            total_chunks += 1

        logger.info(f"✅ {title[:40]}: {len(article_chunks)} chunks")

    logger.info(f"📊 Total chunks created: {total_chunks}")
    return chunks


def save_chunks(chunks: List[ArticleChunk], output_file: str = "articles_chunked.json") -> str:
    """Save chunks to JSON file."""
    output_path = PROCESSED_DIR / output_file
    
    chunks_data = [asdict(chunk) for chunk in chunks]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📁 Saved {len(chunks)} chunks to {output_path}")
    return str(output_path)


def main():
    """Main execution."""
    print("\n🔪 Article Chunker (512 tokens, 50-token overlap)\n")
    
    chunks = chunk_articles()
    if not chunks:
        logger.error("No chunks created!")
        return

    output_path = save_chunks(chunks)
    
    # Statistics
    total_tokens = sum(c.token_count for c in chunks)
    avg_tokens = total_tokens / len(chunks) if chunks else 0
    
    print(f"\n📊 Chunking Complete:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Avg tokens/chunk: {avg_tokens:.1f}")
    print(f"  Output: {output_path}")
    print(f"\n📝 Next: python ingest_pinecone.py\n")


if __name__ == "__main__":
    main()
