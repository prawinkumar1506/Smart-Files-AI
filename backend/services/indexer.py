#
import os
import hashlib
import json
from pathlib import Path
from typing import AsyncGenerator, Tuple, Dict, Any
import logging
import asyncio
from datetime import datetime
import traceback

from .vector_store import VectorStore
from .embedding_service import EmbeddingService
from .file_processors import FileProcessorFactory

logger = logging.getLogger(__name__)

class FileIndexer:
    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService, llm_client=None):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.llm_client = llm_client
        # Initialize the file processor factory with the LLM client
        FileProcessorFactory.initialize(llm_client)
        self.supported_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json',
            '.pdf', '.docx', '.doc', '.rtf', '.odt', '.xml', '.yaml', '.yml', '.c', '.pptx',
            '.csv', '.tsv', '.xlsx',
            '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif', '.svg'
        }
        logger.info(f" FileIndexer initialized with supported extensions: {self.supported_extensions}")

    async def count_files(self, folder_path: str) -> int:
        """Count the number of supported files in a folder"""
        count = 0
        folder_path = Path(folder_path)

        logger.info(f"Counting files in: {folder_path}")

        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() in self.supported_extensions:
                        count += 1

            logger.info(f"Found {count} supported files in {folder_path}")
            return count

        except Exception as e:
            logger.error(f"Error counting files in {folder_path}: {str(e)}")
            return 0

    async def index_folder(self, folder_path: str) -> AsyncGenerator[Tuple[Path, int], None]:
        """Index all supported files in a folder"""
        folder_path = Path(folder_path)

        logger.info(f"Starting to index folder: {folder_path}")

        if not folder_path.exists() or not folder_path.is_dir():
            logger.error(f"Invalid folder path: {folder_path}")
            raise ValueError(f"Invalid folder path: {folder_path}")

        # Add folder to database
        folder_id = await self.vector_store.add_folder(str(folder_path))
        logger.info(f"Added folder to database with ID: {folder_id}")

        processed_count = 0

        try:
            for root, dirs, files in os.walk(folder_path):
                logger.debug(f"Processing directory: {root}")

                for file_name in files:
                    file_path = Path(root) / file_name

                    # Skip Office temporary/lock files (e.g., ~$*.docx/pptx/xlsx)
                    if file_name.startswith("~$"):
                        logger.debug(f"Skipping Office temp file: {file_path}")
                        continue

                    if file_path.suffix.lower() in self.supported_extensions:
                        try:
                            logger.info(f"Processing file: {file_path}")
                            await self._index_file(folder_id, file_path)
                            processed_count += 1
                            yield file_path, processed_count

                            # Add small delay to prevent overwhelming the system
                            await asyncio.sleep(0.01)

                        except Exception as e:
                            logger.error(f"Failed to index {file_path}: {str(e)}")
                            logger.error(f"Traceback: {traceback.format_exc()}")
                            continue
                    else:
                        logger.debug(f"Skipping unsupported file: {file_path}")

        except Exception as e:
            logger.error(f"Error walking directory {folder_path}: {str(e)}")
            raise

        logger.info(f"Completed indexing folder {folder_path}: {processed_count} files processed")

    async def _index_file(self, folder_id: int, file_path: Path):
        """Index a single file"""
        try:
            logger.debug(f"Starting to index file: {file_path}")

            # Get file info
            stat = file_path.stat()
            file_info = {
                'name': file_path.name,
                'type': file_path.suffix.lower(),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'hash': self._calculate_file_hash(file_path)
            }

            logger.debug(f"File info: {file_info}")

            # Add file to database
            file_id = await self.vector_store.add_file(folder_id, str(file_path), file_info)
            logger.debug(f"Added file to database with ID: {file_id}")

            # Get the processor for this file type
            processor = FileProcessorFactory.get_processor(file_path.suffix.lower())
            logger.debug(f"Using processor: {type(processor).__name__}")

            # Check if this is an image file
            is_image_file = file_path.suffix.lower() in {
                '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif'
            }

            if is_image_file and hasattr(processor, 'get_image_embedding'):
                # Fast image processing using only Ollama LLaVA (skip LLM to save time)
                logger.info(f"Processing image file with LLaVA: {file_path}")

                # Get caption and metadata from image processor (Ollama LLaVA)
                content = await processor.extract_text(file_path)
                caption = ""
                metadata = {}
                
                try:
                    content_data = json.loads(content)
                    caption = content_data.get("caption", "")
                    metadata = content_data.get("metadata", {})
                    analysis = content_data.get("analysis", {})
                    if analysis:
                        metadata["analysis"] = analysis
                    if "tags" not in metadata and analysis:
                        metadata["tags"] = [
                            tag for tag in (analysis.get("objects") or [])
                            if isinstance(tag, str)
                        ]
                except json.JSONDecodeError:
                    pass

                # Extract image resolution using PIL
                try:
                    from PIL import Image as PILImage
                    img = PILImage.open(file_path)
                    width, height = img.size
                    metadata["resolution"] = f"{width}x{height}"
                    logger.debug(f"Extracted image resolution: {width}x{height}")
                except Exception as e:
                    logger.debug(f"Could not extract image resolution: {e}")

                # Store the image metadata and caption
                # Include date_modified from filesystem
                date_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                image_metadata = {
                    "caption": caption or "Image indexed",  # Use default caption if none
                    "metadata": {
                        **metadata,
                        "date_modified": date_modified,
                        "file_name": file_path.name
                    },
                    "file_info": file_info
                }

                # Get image embeddings
                embedding_result = await processor.get_image_embedding(file_path)

                # Store the image embeddings
                if embedding_result["text_embedding"] is not None:
                    await self.vector_store.add_image_embedding(
                        file_id,
                        embedding_result["text_embedding"],
                        embedding_result["text_embedding"],
                        image_metadata
                    )
                    logger.info(f"Successfully indexed image {file_path} with caption: {image_metadata['caption'][:80]}")
                else:
                    logger.error(f"Failed to generate text embedding for image {file_path}")
            else:
                # Regular text processing for non-image files
                content = await processor.extract_text(file_path)

                if not content or not content.strip():
                    logger.warning(f"No content extracted from {file_path}")
                    return

                logger.debug(f"Extracted content length: {len(content)} characters")

                # Split content into chunks
                chunks = self._split_text(content)
                logger.debug(f"Split content into {len(chunks)} chunks")

                # Generate embeddings and store chunks
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # Only process non-empty chunks
                        try:
                            logger.debug(f"Generating embedding for chunk {i+1}/{len(chunks)}")
                            embedding = await self.embedding_service.generate_embedding(f"passage: {chunk}")
                            await self.vector_store.add_document_chunk(file_id, i, chunk, embedding)
                            logger.debug(f"Stored chunk {i+1} with embedding")
                        except Exception as e:
                            logger.error(f"Error processing chunk {i} of {file_path}: {str(e)}")
                            continue

                logger.info(f"Successfully indexed {file_path} with {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {str(e)}")
            return ""

    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + chunk_size // 2, end - 200), -1):
                    if text[i] in '.!?\n':
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

            if start >= len(text):
                break

        logger.debug(f"Split text of {len(text)} chars into {len(chunks)} chunks")
        return chunks
