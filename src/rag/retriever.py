"""
Core Retrieval Logic.
This module is responsible for taking a user query, embedding it, and fetching the most
relevant document chunks from the vector store.
"""

from abc import ABC, abstractmethod

from config.logging_config import setup_logger
from rag.embeddings import ModelSelector
from rag.vector_store import BaseVectorStore

logger = setup_logger(__name__)


class BaseRetriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        pass


class DenseRetriever(BaseRetriever):
    def __init__(self, vector_store: BaseVectorStore, reranker=None):
        self.vector_store = vector_store
        self.reranker = reranker

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        logger.info(f"Retrieving top {top_k} documents for query: '{query}'")
        try:
            fetch_k = top_k * 4 if self.reranker else top_k

            query_embedding = await ModelSelector.get_single_embedding(query)
            results = self.vector_store.search(query_embedding, top_k=fetch_k)
            logger.info(f"Initial Retrieval fetched {len(results)}.")

            if self.reranker and results:
                logger.info("Reranking results using the configured reranker.")
                results = self.reranker.rerank(query, results, top_k=top_k)
                logger.info(f"Reranking completed. Returning top {len(results)} results.")
            return results
        

        except Exception as e:
            logger.error(f"Error occurred while retrieving documents: {e}")
            raise