import os
import tempfile
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from src.common.logger import logger


class ConversionUtils:
    @staticmethod
    async def convert_pdf_to_text(pdf_path: str) -> str:
        """Convert PDF to text using PyPDFLoader"""
        try:
            loader = PyPDFLoader(pdf_path)
            pages = []
            async for page in loader.alazy_load():
                pages.append(page.page_content)
            return "\n".join(pages)
        except Exception as e:
            logger.error(f"Failed to convert PDF to text: {e}")
            raise

    @staticmethod
    def chunk_text(
        text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[str]:
        """Split text into chunks for embedding"""
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""],
            )
            chunks = text_splitter.split_text(text)
            logger.info(f"Split text into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Failed to chunk text: {e}")
            raise

    @staticmethod
    def create_temp_file(file_bytes: bytes, suffix: str = ".pdf") -> str:
        """Create a temporary file and return its path"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(file_bytes)
            temp_file.close()
            logger.info(f"Created temporary file: {temp_file.name}")
            return temp_file.name
        except Exception as e:
            logger.error(f"Failed to create temporary file: {e}")
            raise

    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        """Delete temporary file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup temporary file {file_path}: {e}")
            # Don't raise here as cleanup failures shouldn't break the main flow
