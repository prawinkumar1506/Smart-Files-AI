
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: Optional[str] = Field(None, env='GEMINI_API_KEY')
    
    # Qdrant Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_PATH: Optional[str] = "local_qdrant" # For local embedded mode
    USE_LOCAL_QDRANT: bool = True
    
    # Collections
    COLLECTION_TEXT: str = "clinical_text_memory"
    COLLECTION_IMAGE: str = "clinical_image_memory"
    COLLECTION_INTERACTION: str = "interaction_memory"
    COLLECTION_GUIDELINES: str = "guidelines_memory"
    
    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    
    # Paths
    UPLOAD_DIR: str = "uploads"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
