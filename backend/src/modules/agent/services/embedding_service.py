from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_openai import OpenAIEmbeddings
from src.common.config import settings
from src.common.logger import logger
from src.database.postgres.postgres_client import postgres_client
from src.database.storage_bucket.storage_bucket_client import storage_bucket_client
from src.modules.agent.repositories.agent_repository import AgentRepository
from src.modules.agent.repositories.embedding_repository import embedding_repository
from src.modules.agent.utils.conversion_utils import ConversionUtils


class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY,
        )
        self.embedding_repository = embedding_repository
        self.storage_client = storage_bucket_client

    async def embed_resume(
        self, user_id: str, agent_id: str = None, resume_id: str = None
    ) -> bool:
        """
        Coordinate the embedding process for a resume.

        This service orchestrates the embedding workflow but delegates
        specific responsibilities to other services.

        Args:
            user_id: The user ID
            agent_id: The agent ID (if provided, resume_id will be fetched from agent)
            resume_id: The resume ID (if provided directly, agent_id is optional)
        """
        temp_file_path = None
        inserted_point_ids = []
        final_resume_id = None

        try:
            # Step 1: Determine resume_id
            if resume_id:
                final_resume_id = resume_id
                logger.info(f"Using provided resume_id={resume_id}")
            elif agent_id:
                final_resume_id = await self._get_resume_id_from_agent_id(agent_id)
                if not final_resume_id:
                    logger.error(f"No resume found for agent_id={agent_id}")
                    return False
                logger.info(
                    f"Retrieved resume_id={final_resume_id} from agent_id={agent_id}"
                )
            else:
                logger.error("Either agent_id or resume_id must be provided")
                return False

            # Step 2: Download and create temp file
            storage_path = f"{user_id}/{final_resume_id}"
            temp_file_path = await self._download_and_create_temp_file(storage_path)

            # Step 3: Convert PDF to text
            logger.info(f"Converting PDF to text for resume_id={final_resume_id}")
            text = await ConversionUtils.convert_pdf_to_text(temp_file_path)

            # Step 4: Chunk the text
            logger.info(f"Chunking text for resume_id={final_resume_id}")
            text_chunks = ConversionUtils.chunk_text(text)

            # Step 5: Generate embeddings
            logger.info(f"Generating embeddings for {len(text_chunks)} chunks")
            embeddings = await self._generate_embeddings(text_chunks)

            # Step 6: Prepare metadata
            metadata_list = self._prepare_metadata(
                text_chunks, user_id, final_resume_id, agent_id
            )

            # Step 7: Store embeddings via repository (using LangChain)
            logger.info(f"Storing embeddings in Qdrant for resume_id={final_resume_id}")
            inserted_point_ids = self.embedding_repository.upsert_embeddings(
                collection_name="resumes",
                texts=text_chunks,
                metadata=metadata_list,
            )

            logger.info(
                f"Successfully embedded resume_id={final_resume_id} with {len(inserted_point_ids)} chunks"
            )
            return True

        except Exception as e:
            identifier = (
                f"agent_id={agent_id}" if agent_id else f"resume_id={resume_id}"
            )
            logger.error(f"Failed to embed resume for {identifier}: {e}")

            # Cleanup: Delete any embeddings that were inserted
            if inserted_point_ids and final_resume_id:
                try:
                    logger.info(
                        f"Cleaning up {len(inserted_point_ids)} inserted embeddings for {identifier}"
                    )
                    self.embedding_repository.delete_embeddings_by_resume_id(
                        "resumes", final_resume_id
                    )
                except Exception as cleanup_error:
                    logger.error(
                        f"Failed to cleanup embeddings for {identifier}: {cleanup_error}"
                    )

            return False

        finally:
            # Always cleanup temporary file
            if temp_file_path:
                ConversionUtils.cleanup_temp_file(temp_file_path)

    async def _get_resume_id_from_agent_id(self, agent_id: str) -> Optional[str]:
        """Get resume_id from agent_id using database query"""
        try:
            # Get database session
            db_session = next(postgres_client.get_db())
            agent_repository = AgentRepository(db_session)

            # Get agent by ID
            agent = agent_repository.get_agent_by_id(UUID(agent_id))

            if not agent:
                logger.error(f"Agent not found with agent_id={agent_id}")
                return None

            if not agent.curr_resume_id:
                logger.error(f"No resume associated with agent_id={agent_id}")
                return None

            resume_id = str(agent.curr_resume_id)
            logger.info(f"Found resume_id={resume_id} for agent_id={agent_id}")
            return resume_id

        except Exception as e:
            logger.error(f"Failed to get resume_id for agent_id={agent_id}: {e}")
            return None

    async def _download_and_create_temp_file(self, storage_path: str) -> str:
        """Download file from storage and create a temporary file"""
        try:
            # Download file from storage
            file_bytes = await self.storage_client.download_bytes_from_path(
                storage_path
            )

            # Create temporary file
            temp_file_path = ConversionUtils.create_temp_file(file_bytes)

            logger.info(f"Downloaded and created temp file: {temp_file_path}")
            return temp_file_path

        except Exception as e:
            logger.error(
                f"Failed to download and create temp file for {storage_path}: {e}"
            )
            raise

    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def _prepare_metadata(
        self, text_chunks: List[str], user_id: str, resume_id: str, agent_id: str = None
    ) -> List[Dict[str, Any]]:
        """Prepare metadata for each text chunk"""
        metadata_list = []

        for i, chunk in enumerate(text_chunks):
            metadata = {
                "user_id": user_id,
                "resume_id": resume_id,
                "chunk_index": i,
                "chunk_size": len(chunk),
                "total_chunks": len(text_chunks),
            }

            if agent_id:
                metadata["agent_id"] = agent_id

            metadata_list.append(metadata)

        return metadata_list

    async def delete_resume_embeddings(
        self, agent_id: str = None, resume_id: str = None
    ) -> bool:
        """Delete all embeddings for a specific resume"""
        try:
            final_resume_id = None

            if resume_id:
                final_resume_id = resume_id
                logger.info(f"Using provided resume_id={resume_id}")
            elif agent_id:
                final_resume_id = await self._get_resume_id_from_agent_id(agent_id)
                if not final_resume_id:
                    logger.error(f"No resume found for agent_id={agent_id}")
                    return False
                logger.info(
                    f"Retrieved resume_id={final_resume_id} from agent_id={agent_id}"
                )
            else:
                logger.error("Either agent_id or resume_id must be provided")
                return False

            success = self.embedding_repository.delete_embeddings_by_resume_id(
                "resumes", final_resume_id
            )
            identifier = (
                f"agent_id={agent_id}" if agent_id else f"resume_id={resume_id}"
            )
            logger.info(
                f"Deleted embeddings for {identifier} (resume_id={final_resume_id})"
            )
            return success
        except Exception as e:
            identifier = (
                f"agent_id={agent_id}" if agent_id else f"resume_id={resume_id}"
            )
            logger.error(f"Failed to delete embeddings for {identifier}: {e}")
            return False

    def similarity_search(
        self,
        query: str,
        collection_name: str = "resumes",
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform similarity search across all resumes"""
        try:
            results = self.embedding_repository.similarity_search(
                query=query,
                collection_name=collection_name,
                k=k,
                filter_dict=filter_dict,
            )
            logger.info(f"Performed similarity search with query: '{query}'")
            return results
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
        """Perform similarity search within a specific resume"""
        try:
            results = self.embedding_repository.similarity_search_by_resume_id(
                query=query,
                resume_id=resume_id,
                collection_name=collection_name,
                k=k,
            )
            logger.info(
                f"Performed similarity search for resume_id={resume_id} with query: '{query}'"
            )
            return results
        except Exception as e:
            logger.error(
                f"Failed to perform similarity search for resume_id={resume_id}: {e}"
            )
            raise

    async def similarity_search_by_agent_id(
        self,
        query: str,
        agent_id: str,
        collection_name: str = "resumes",
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Perform similarity search within a specific agent's resume"""
        try:
            # Get resume_id from agent_id
            resume_id = await self._get_resume_id_from_agent_id(agent_id)
            if not resume_id:
                logger.error(f"No resume found for agent_id={agent_id}")
                return []

            results = self.embedding_repository.similarity_search_by_resume_id(
                query=query,
                resume_id=resume_id,
                collection_name=collection_name,
                k=k,
            )
            logger.info(
                f"Performed similarity search for agent_id={agent_id} (resume_id={resume_id}) with query: '{query}'"
            )
            return results
        except Exception as e:
            logger.error(
                f"Failed to perform similarity search for agent_id={agent_id}: {e}"
            )
            raise

    def similarity_search_by_user_id(
        self,
        query: str,
        user_id: str,
        collection_name: str = "resumes",
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Perform similarity search across all resumes of a specific user"""
        try:
            results = self.embedding_repository.similarity_search_by_user_id(
                query=query,
                user_id=user_id,
                collection_name=collection_name,
                k=k,
            )
            logger.info(
                f"Performed similarity search for user_id={user_id} with query: '{query}'"
            )
            return results
        except Exception as e:
            logger.error(
                f"Failed to perform similarity search for user_id={user_id}: {e}"
            )
            raise

    def get_collection_stats(self, collection_name: str = "resumes") -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            stats = self.embedding_repository.get_collection_stats(collection_name)
            logger.info(f"Retrieved stats for collection: {collection_name}")
            return stats
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise

    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            collections = self.embedding_repository.list_collections()
            logger.info(f"Listed {len(collections)} collections")
            return collections
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise


embedding_service = EmbeddingService()
