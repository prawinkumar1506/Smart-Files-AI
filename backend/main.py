
import asyncio
import os
import sys
import logging
import traceback
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to Python path so `backend` is a proper package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.orchestrator import OrchestratorAgent
from backend.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartFile AI - Multi-Agent System", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Orchestrator
orchestrator: Optional[OrchestratorAgent] = None

class IngestRequest(BaseModel):
    files: List[str] # List of absolute file paths

class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

@app.on_event("startup")
async def startup_event():
    global orchestrator
    try:
        logger.info("Initializing Agent Orchestrator...")
        orchestrator = OrchestratorAgent()
        logger.info("System Initialized Successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        traceback.print_exc()

@app.get("/")
async def root():
    return {"message": "SmartFile AI MAS Backend Running", "status": "active"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/ingest")
async def ingest_files(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Trigger the ingestion agent workflow.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # We can run this in background
    # background_tasks.add_task(orchestrator.run_ingestion_flow, request.files)
    
    # Or run/await it to return status (better for immediate feedback in this context)
    try:
        result = await orchestrator.run_ingestion_flow(request.files)
        return result
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def query_system(request: QueryRequest):
    """
    Trigger the retrieval and reasoning agent workflow.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
        
    try:
        result = await orchestrator.run_query_flow(request.query, request.filters)
        return result
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Maintain some compatibility or add helper stats
@app.get("/api/status")
async def get_status():
    if not orchestrator:
        return {"status": "initializing"}
    return {"status": "ready", "backend": "Multi-Agent Qdrant Architecture"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
