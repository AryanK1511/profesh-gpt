from typing import Any, Dict, List, Optional

from src.common.logger import logger
from src.database.qdrant.qdrant_client import qdrant_client


class EmbeddingRepository:
    def __init__(self):
        self.qdrant_client = qdrant_client

    def upsert_embeddings(
        self,
        collection_name: str,
        texts: List[str],
        metadata: List[Dict[str, Any]],
    ) -> List[str]:
        try:
            qdrant_store = self.qdrant_client.get_langchain_qdrant(collection_name)

            ids = qdrant_store.add_documents(
                texts=texts,
                metadatas=metadata,
            )

            logger.info(f"Successfully upserted {len(ids)} embeddings using LangChain")
            return ids
        except Exception as e:
            logger.error(f"Failed to upsert embeddings with LangChain: {e}")
            raise

    def similarity_search(
        self,
        query: str,
        collection_name: str = "resumes",
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            qdrant_store = self.qdrant_client.get_langchain_qdrant(collection_name)

            results = qdrant_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict,
            )

            formatted_results = []
            for doc, score in results:
                formatted_results.append(
                    {
                        "text": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score,
                    }
                )

            logger.info(
                f"Successfully performed similarity search with {len(formatted_results)} results"
            )
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            raise

    def similarity_search_by_resume_id(
        self,
        query: str,
        resume_id: str,
        collection_name: str = "resumes",
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        filter_dict = {"resume_id": resume_id}
        return self.similarity_search(query, collection_name, k, filter_dict)

    def similarity_search_by_user_id(
        self,
        query: str,
        user_id: str,
        collection_name: str = "resumes",
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        filter_dict = {"user_id": user_id}
        return self.similarity_search(query, collection_name, k, filter_dict)

    def delete_embeddings_by_resume_id(
        self, collection_name: str, resume_id: str
    ) -> bool:
        try:
            self.qdrant_client.client.delete(
                collection_name=collection_name,
                points_selector={
                    "filter": {
                        "must": [{"key": "resume_id", "match": {"value": resume_id}}]
                    }
                },
            )

            logger.info(f"Successfully deleted embeddings for resume_id: {resume_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting embeddings for resume_id {resume_id}: {e}")
            return False


embedding_repository = EmbeddingRepository()
