from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

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

# New schemas for File Organiser
class FolderHierarchy(BaseModel):
    id: int
    path: str
    name: str
    parent_id: Optional[int] = None
    level: int
    file_count: int
    subfolder_count: int
    last_modified: str
    children: List['FolderHierarchy'] = []

class FileClassification(BaseModel):
    file_id: int
    file_path: str
    file_name: str
    file_type: str
    classification: str
    confidence: float
    suggested_folder: str
    reasoning: str

class OrganiseRequest(BaseModel):
    folder_id: int
    dry_run: Optional[bool] = True

class OrganiseResponse(BaseModel):
    success: bool
    message: str
    classifications: List[FileClassification]
    suggested_structure: Dict[str, List[str]]
    total_files: int

class OrganiseAction(BaseModel):
    id: int
    folder_id: int
    action_type: str  # 'move', 'create_folder', 'classify'
    source_path: str
    target_path: str
    classification: str
    confidence: float
    timestamp: datetime
    status: str  # 'pending', 'completed', 'failed', 'rolled_back'

class ExecuteOrganiseRequest(BaseModel):
    folder_id: int
    actions: List[Dict[str, Any]]
    confirm: bool = False

class RollbackRequest(BaseModel):
    action_id: int

# Update FolderHierarchy to handle forward references
FolderHierarchy.model_rebuild()
