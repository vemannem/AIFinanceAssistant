"""RAG Retrieval Engine - Query Pinecone for knowledge."""

from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from src.core.config import Config
from src.core.logger import get_logger
from src.core.llm_provider import get_llm_provider
from src.core import RAGError

logger = get_logger(__name__, Config.LOG_LEVEL)


class RAGRetriever:
    """Query Pinecone vector database for relevant articles."""
    
    def __init__(self):
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index = self.pc.Index(Config.PINECONE_INDEX_NAME)
        self.llm = get_llm_provider()
        self.top_k = Config.RAG_RETRIEVAL_TOP_K
        self.min_score = Config.RAG_MIN_RELEVANCE_THRESHOLD
    
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks from Pinecone.
        
        Args:
            query: User query text
            top_k: Number of results (default from config)
            category_filter: Optional category filter
        
        Returns:
            List of chunks with metadata and relevance scores
        """
        try:
            # Embed query
            query_embedding = await self.llm.embed([query])
            query_vector = query_embedding[0]
            
            # Query Pinecone
            k = top_k or self.top_k
            
            # Build filter if category specified
            filter_dict = None
            if category_filter:
                filter_dict = {"category": {"$eq": category_filter}}
            
            results = self.index.query(
                vector=query_vector,
                top_k=k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results, filter by relevance threshold
            chunks = []
            for match in results.matches:
                logger.info(f"Match score: {match.score} (threshold: {self.min_score})")
                if match.score >= self.min_score:
                    # Note: We don't store chunk content in metadata, 
                    # so we use a placeholder. In production, we'd retrieve from a database.
                    chunk = {
                        "content": f"[Retrieved content from {match.metadata.get('article_title')}]",
                        "score": match.score,
                        "metadata": {
                            "article_title": match.metadata.get("article_title"),
                            "category": match.metadata.get("category"),
                            "source_url": match.metadata.get("source_url"),
                            "publish_date": match.metadata.get("publish_date"),
                            "source": match.metadata.get("source"),
                        }
                    }
                    chunks.append(chunk)
            
            logger.info(f"Retrieved {len(chunks)} chunks for query: {query[:50]}")
            return chunks
            
        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise RAGError(f"Failed to retrieve from RAG: {str(e)}")
    
    def format_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format retrieved chunks as citations.
        
        Args:
            chunks: Retrieved chunks
        
        Returns:
            List of citation dicts
        """
        seen_urls = set()
        citations = []
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            url = metadata.get("source_url", "")
            title = metadata.get("article_title", "Unknown")
            category = metadata.get("category", "general")
            
            # Avoid duplicate citations
            if url and url not in seen_urls:
                citations.append({
                    "title": title,
                    "source_url": url,
                    "category": category,
                })
                seen_urls.add(url)
        
        return citations


# Singleton instance
_retriever = None


def get_rag_retriever() -> RAGRetriever:
    """Get singleton RAG retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever
