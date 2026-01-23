#backend\services\file_processors.py
import os
import json
from pathlib import Path
from typing import Protocol, Dict
import logging

logger = logging.getLogger(__name__)

class FileProcessor(Protocol):
    async def extract_text(self, file_path: Path) -> str:
        """Extract text content from a file"""
        ...

class TextFileProcessor:
    """Processor for plain text files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {str(e)}")
            return ""

class PDFProcessor:
    """Processor for PDF files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            logger.warning("PyPDF2 not installed, skipping PDF processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {str(e)}")
            return ""

class DocxProcessor:
    """Processor for DOCX files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            logger.warning("python-docx not installed, skipping DOCX processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading DOCX file {file_path}: {str(e)}")
            return ""

class PPTXProcessor:
    """Processor for PPTX files"""

    async def extract_text(self, file_path: Path) -> str:
        try:
            import pptx
            prs = pptx.Presentation(file_path)
            text = ""
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            return text
        except ImportError:
            logger.warning("python-pptx not installed, skipping PPTX processing")
            return ""
        except Exception as e:
            logger.error(f"Error reading PPTX file {file_path}: {str(e)}")
            return ""

class ImageProcessor:
    """Processor for image files using Gemini LLM for captioning"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        logger.info("ImageProcessor initialized with Gemini LLM client")

    async def extract_text(self, file_path: Path) -> str:
        """Extract text content from an image file using Gemini LLM for detailed captioning"""
        try:
            from PIL import Image
            import base64
            import io

            # Open the image
            raw_image = Image.open(file_path).convert('RGB')

            # Extract basic metadata
            metadata = self._extract_image_metadata(file_path)

            # Generate detailed caption using Gemini LLM
            detailed_caption = "A detailed description of the image will be generated here."

            if self.llm_client:
                try:
                    # Create a detailed prompt for image description
                    prompt = f"""
                    You are an expert image description assistant. Provide a detailed 4-5 sentence description of this image.
                    Image filename: {file_path.name}
                    Image metadata: {json.dumps(metadata)}

                    Your detailed description should:
                    1. Be 4-5 complete sentences
                    2. Include all important visual elements
                    3. Describe the context and purpose of the image
                    4. Be clear, accurate, and professional
                    """

                    # Generate the caption using the LLM client
                    response = await self.llm_client.generate_answer(
                        question=f"Describe this image in detail: {file_path.name}",
                        context=f"Image metadata: {json.dumps(metadata)}"
                    )

                    if response and response.strip():
                        detailed_caption = response.strip()
                        logger.info(f"Generated caption for {file_path.name}: {detailed_caption[:100]}...")
                except Exception as e:
                    logger.error(f"Error generating detailed caption with Gemini: {str(e)}")
                    detailed_caption = f"Error generating caption: {str(e)}"

            # Return structured data as JSON string
            return json.dumps({
                "caption": detailed_caption,
                "metadata": metadata
            })

        except Exception as e:
            logger.error(f"Error processing image file {file_path}: {str(e)}")
            return json.dumps({
                "caption": f"Error processing image: {str(e)}",
                "metadata": self._extract_image_metadata(file_path)
            })

    def _extract_image_metadata(self, file_path: Path) -> Dict:
        """Extract basic metadata from image file"""
        try:
            from PIL import Image
            import os

            with Image.open(file_path) as img:
                return {
                    "format": img.format,
                    "size": img.size,
                    "mode": img.mode,
                    "file_size": os.path.getsize(file_path),
                    "file_name": os.path.basename(file_path)
                }
        except Exception as e:
            logger.error(f"Error extracting image metadata {file_path}: {str(e)}")
            return {
                "format": "",
                "size": "",
                "mode": "",
                "file_size": os.path.getsize(file_path),
                "file_name": os.path.basename(file_path)
            }

    async def get_image_embedding(self, file_path: Path) -> Dict:
        """Generate text embedding for the image caption"""
        try:
            from services.embedding_service import EmbeddingService
            import numpy as np

            # Get the caption from the image
            caption_data = json.loads(await self.extract_text(file_path))
            caption = caption_data["caption"]

            # If caption is empty or default, generate a better one
            if not caption or caption.startswith("A detailed description") or caption.startswith("Error"):
                logger.info(f"No valid caption found for {file_path}, generating a new one")
                if self.llm_client:
                    try:
                        prompt = f"""
                        Provide a detailed 4-5 sentence description of an image with filename: {file_path.name}.
                        Include all important visual elements, describe the context and purpose of the image.
                        Be clear, accurate, and professional.
                        """
                        caption = await self.llm_client.generate_answer(
                            question=f"Describe this image: {file_path.name}",
                            context=f"Filename: {file_path.name}"
                        )
                        logger.info(f"Generated new caption for {file_path.name}: {caption[:100]}...")
                    except Exception as e:
                        logger.error(f"Error generating caption with LLM: {str(e)}")
                        caption = f"Error generating caption: {str(e)}"

            # Generate text embedding for the caption using the embedding service
            embedding_service = EmbeddingService()
            text_embedding = await embedding_service.generate_embedding(f"image: {caption}")

            # Convert to numpy array if it's not already
            if text_embedding is not None and not isinstance(text_embedding, np.ndarray):
                text_embedding = np.array(text_embedding)

            return {
                "image_embedding": None,  # We're not using image embeddings anymore
                "text_embedding": text_embedding,
                "caption": caption
            }

        except Exception as e:
            logger.error(f"Error generating text embedding for image {file_path}: {str(e)}")
            return {
                "image_embedding": None,
                "text_embedding": None,
                "caption": ""
            }

class FileProcessorFactory:
    """Factory for creating file processors"""

    _processors = {
        '.txt': TextFileProcessor(),
        '.md': TextFileProcessor(),
        '.py': TextFileProcessor(),
        '.js': TextFileProcessor(),
        '.html': TextFileProcessor(),
        '.css': TextFileProcessor(),
        '.json': TextFileProcessor(),
        '.pdf': PDFProcessor(),
        '.docx': DocxProcessor(),
        '.doc': DocxProcessor(),
        '.pptx': PPTXProcessor(),
    }

    _image_processor = None

    @classmethod
    def initialize(cls, llm_client=None):
        """Initialize the factory with an LLM client for image processing"""
        if llm_client:
            cls._image_processor = ImageProcessor(llm_client=llm_client)
        else:
            cls._image_processor = ImageProcessor()

    @classmethod
    def get_processor(cls, file_extension: str) -> FileProcessor:
        """Get appropriate processor for file extension"""
        # Handle image extensions
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif']
        if file_extension.lower() in image_extensions:
            if cls._image_processor is None:
                cls._image_processor = ImageProcessor()
            return cls._image_processor

        # Default to text processor for other extensions
        processor = cls._processors.get(file_extension.lower())
        if processor is None:
            return cls._processors['.txt']
        return processor
