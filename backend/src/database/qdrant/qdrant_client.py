from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from src.common.config import settings
from src.common.logger import logger


class QdrantDBClient:
    def __init__(self):
        try:
            if settings.PYTHON_ENV.lower() == "prod":
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    check_compatibility=False,
                )
            elif settings.PYTHON_ENV.lower() == "dev":
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    check_compatibility=False,
                )

            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY,
            )

            self.create_resume_collection_if_not_exists()

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise

    def create_resume_collection_if_not_exists(
        self, collection_name: str = "resumes"
    ) -> None:
        try:
            collections = self.client.get_collections()
            collection_names = [
                collection.name for collection in collections.collections
            ]

            if collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=1536,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"Qdrant collection '{collection_name}' already exists")

        except Exception as e:
            logger.error(f"Failed to create resume collection: {e}")
            raise

    def get_langchain_qdrant(self, collection_name: str = "resumes") -> Qdrant:
        try:
            return Qdrant(
                client=self.client,
                collection_name=collection_name,
                embeddings=self.embeddings,
            )
        except Exception as e:
            logger.error(f"Failed to create LangChain Qdrant instance: {e}")
            raise


qdrant_client = QdrantDBClient()
