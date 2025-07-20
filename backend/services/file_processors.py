
#backend\services\file_processors.py
import os
from pathlib import Path
from typing import Protocol
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
    }
    
    @classmethod
    def get_processor(cls, file_extension: str) -> FileProcessor:
        """Get appropriate processor for file extension"""
        processor = cls._processors.get(file_extension.lower())
        if processor is None:
            # Default to text processor
            return cls._processors['.txt']
        return processor
