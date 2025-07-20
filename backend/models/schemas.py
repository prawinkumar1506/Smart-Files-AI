from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class IndexRequest(BaseModel):
    folder_paths: List[str]

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    threshold: Optional[float] = 0.7

class QueryRequest(BaseModel):
    question: str

class IndexResponse(BaseModel):
    success: bool
    message: str
    indexed_files: int

class SearchResult(BaseModel):
    file_path: str
    content: str
    similarity_score: float
    file_type: str
    last_modified: str

class SearchResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    total_results: int

class QuerySource(BaseModel):
    file_path: str
    content_preview: str
    similarity_score: float

class QueryResponse(BaseModel):
    success: bool
    answer: str
    sources: List[QuerySource]

class FolderInfo(BaseModel):
    id: int
    path: str
    file_count: int
    last_indexed: str

class IndexStatus(BaseModel):
    is_indexing: bool
    progress: int
    current_file: str
