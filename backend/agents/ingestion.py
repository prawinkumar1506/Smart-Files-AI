
import os
from typing import Dict, Any, Optional, List
from backend.agents.base import BaseAgent
from backend.memory.vector_memory import VectorMemory
from backend.core.config import settings
import PyPDF2
from concurrent.futures import ThreadPoolExecutor

class IngestionAgent(BaseAgent):
    def __init__(self, vector_memory: VectorMemory):
        super().__init__("IngestionAgent")
        self.memory = vector_memory
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Ingest a file or list of files.
        
        Args:
            input_data: {
                "file_paths": List[str]
            }
        """
        file_paths = input_data.get("file_paths", [])
        results = {
            "processed": [],
            "failed": []
        }
        
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    results["failed"].append({"path": file_path, "reason": "File not found"})
                    continue
                
                # Check file type
                ext = os.path.splitext(file_path)[1].lower()
                content = ""
                
                if ext == ".pdf":
                    content = self._parse_pdf(file_path)
                elif ext in [".txt", ".md", ".json"]:
                    content = self._parse_text(file_path)
                else:
                    results["failed"].append({"path": file_path, "reason": "Unsupported format"})
                    continue
                
                if not content.strip():
                     results["failed"].append({"path": file_path, "reason": "Empty content"})
                     continue

                # Chunking (Simple overlap fixed size)
                chunks = self._chunk_text(content)
                
                # Upsert Chunks
                for i, chunk in enumerate(chunks):
                    metadata = {
                        "file_path": file_path,
                        "file_name": os.path.basename(file_path),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "doc_type": ext,
                        "modality": "text"
                    }
                    
                    await self.memory.upsert_memory(
                        collection=settings.COLLECTION_TEXT,
                        content=chunk,
                        metadata=metadata
                    )
                
                results["processed"].append(file_path)
                self.log(f"Successfully ingested {file_path} - {len(chunks)} chunks.")

            except Exception as e:
                self.log(f"Error ingesting {file_path}: {str(e)}", level="error")
                results["failed"].append({"path": file_path, "reason": str(e)})
        
        return results

    def _parse_pdf(self, path: str) -> str:
        text = ""
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _parse_text(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
        return chunks
