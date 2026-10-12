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
    session_id: Optional[int] = None
    llm_provider: Optional[str] = "gemini"

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

# Schemas for Chat History
class ChatMessage(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    sources: Optional[List[QuerySource]] = None
    timestamp: datetime

class ChatSession(BaseModel):
    id: int
    session_name: str
    created_at: datetime

class CreateChatSessionRequest(BaseModel):
    session_name: str

class GenerateChatNameRequest(BaseModel):
    message: str
    session_id: int
    llm_provider: Optional[str] = "gemini"

class RenameSessionRequest(BaseModel):
    session_name: str

class ApiKey(BaseModel):
    key: str

class LLMConfig(BaseModel):
    """Configuration for LLM providers"""
    provider: str  # gemini, openrouter, groq, openai, anthropic, ollama
    api_key: Optional[str] = None
    model: Optional[str] = None
    custom_base_url: Optional[str] = None

class LLMProviderInfo(BaseModel):
    """Information about available LLM provider"""
    name: str
    display_name: str
    type: str  # cloud or local
    requires_key: bool
    api_key_name: Optional[str] = None
    env_var: Optional[str] = None
    url: str
    models: List[str]
    default_model: str
    capabilities: List[str]

class SystemRequirement(BaseModel):
    """System requirement check"""
    name: str
    met: bool
    value: Optional[str] = None
    message: str
    critical: bool = False

class SystemRequirementsCheck(BaseModel):
    """System requirements check result"""
    all_requirements_met: bool
    timestamp: datetime
    requirements: List[SystemRequirement]
    warnings: List[str]

class SystemTier(BaseModel):
    """System hardware tier classification"""
    tier: int  # 1 = low-end, 2 = mid-range, 3 = high-end
    tier_name: str  # "Basic", "Performance", "Enthusiast"
    ram_gb: float
    cpu_cores: int
    cpu_frequency_ghz: Optional[float] = None
    gpu_available: bool
    gpu_name: Optional[str] = None
    vram_gb: Optional[float] = None
    recommended_models: List[str]
    tier_description: str

class OllamaModel(BaseModel):
    """Ollama model specification"""
    name: str
    tag: str
    full_name: str  # e.g., "llava:7b"
    display_name: str
    description: str
    size_gb: float
    ram_required_gb: int
    vram_required_gb: Optional[int] = None
    min_tier: int  # Minimum system tier required
    capabilities: List[str]  # ["text", "vision", "code", etc.]
    context_length: int
    parameters: str  # e.g., "7B", "13B"
    quantization: Optional[str] = None
    download_url: str
    is_downloaded: bool = False
    download_progress: float = 0.0

class ModelDownloadRequest(BaseModel):
    """Request to download an Ollama model"""
    model_name: str  # e.g., "llava:7b"
    
class ModelDownloadStatus(BaseModel):
    """Status of model download"""
    model_name: str
    status: str  # "pending", "downloading", "completed", "failed"
    progress: float  # 0.0 to 100.0
    downloaded_bytes: int
    total_bytes: int
    message: str

class InstalledModelsResponse(BaseModel):
    """Response with installed Ollama models"""
    success: bool
    models: List[OllamaModel]
    total_size_gb: float

# Update FolderHierarchy to handle forward references
FolderHierarchy.model_rebuild()