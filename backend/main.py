import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import uvicorn
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import logging
import traceback
import argparse
import socket
from contextlib import asynccontextmanager
import mimetypes

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.indexer import FileIndexer
from services.vector_store import VectorStore
from services.llm_client import LLMClientFactory
from services.file_organiser import FileOrganiser
from services.smart_images_service import SmartImagesService
from models.schemas import (
    IndexRequest, SearchRequest, QueryRequest,
    IndexResponse, SearchResponse, QueryResponse,
    FolderInfo, IndexStatus, FolderHierarchy,
    OrganiseRequest, OrganiseResponse, ExecuteOrganiseRequest,
    ChatSession, ChatMessage, CreateChatSessionRequest,
    GenerateChatNameRequest, ApiKey
)

# Global services
vector_store = None
file_indexer = None
llm_client = None
file_organiser = None
smart_images_service = None
indexing_status = {"is_indexing": False, "progress": 0, "current_file": "", "total_files": 0, "processed_files": 0}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    global vector_store, file_indexer, llm_client, file_organiser, smart_images_service

    # Startup
    try:
        logger.info("=" * 50)
        logger.info("STARTING SMARTFILE AI BACKEND")
        logger.info("=" * 50)

        # Initialize critical services only
        logger.info("Initializing vector store...")
        vector_store = VectorStore()
        await vector_store.initialize()
        logger.info("Vector store initialized successfully")

        logger.info("Initializing file indexer (without embedding model)...")
        file_indexer = FileIndexer(vector_store, vector_store.embedding_service, None)
        logger.info("File indexer initialized successfully")

        # LLM client and smart images service will be initialized lazily on first use
        logger.info("Backend services ready for lazy loading")

        # Check database status
        folders = await vector_store.get_indexed_folders()
        files = await vector_store.get_indexed_files()
        logger.info(f"Database status: {len(folders)} folders, {len(files)} files indexed")

        logger.info("SmartFile AI Backend started successfully!")
        logger.info("=" * 50)

        yield
    except Exception as e:
        logger.error(f"Failed to initialize backend: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down SmartFile AI Backend...")
        try:
            if vector_store:
                await vector_store.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="SmartFile AI Backend",
    version="1.0.0",
    lifespan=lifespan,
    description="AI-powered file indexing and search backend"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js
        "http://127.0.0.1:3000",  # Next.js alternative
        "http://localhost:3001",  # Next.js (Tauri dev)
        "http://127.0.0.1:3001",  # Next.js (Tauri dev) alternative
        "app://*",                # Packaged Electron
        "file://*"                # Local file access
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "SmartFile AI Backend is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    try:
        # Check database connection
        folders = await vector_store.get_indexed_folders()
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "indexed_folders": len(folders)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

async def ensure_llm_client():
    """Lazily initialize LLM client on first use"""
    global llm_client
    if llm_client is None:
        logger.info("Initializing LLM client (lazy load)...")
        llm_client = LLMClientFactory.create_client()
        logger.info("LLM client initialized successfully")
    return llm_client

async def ensure_file_organiser():
    """Lazily initialize file organiser on first use"""
    global file_organiser, llm_client
    if file_organiser is None:
        await ensure_llm_client()
        logger.info("Initializing file organiser (lazy load)...")
        file_organiser = FileOrganiser(vector_store, llm_client)
        logger.info("File organiser initialized successfully")
    return file_organiser

async def ensure_smart_images_service():
    """Lazily initialize smart images service on first use"""
    global smart_images_service, llm_client
    if smart_images_service is None:
        await ensure_llm_client()
        logger.info("Initializing smart images service (lazy load)...")
        smart_images_service = SmartImagesService(vector_store=vector_store, embedding_service=vector_store.embedding_service)
        smart_images_service.llm_client = llm_client
        logger.info("Smart images service initialized successfully")
    return smart_images_service

@app.post("/api/index", response_model=IndexResponse)
async def index_folders(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index the specified folders"""
    logger.info("=" * 50)
    logger.info("INDEXING REQUEST RECEIVED")
    logger.info(f"Folders to index: {request.folder_paths}")
    logger.info("=" * 50)

    if indexing_status["is_indexing"]:
        logger.warning("Indexing already in progress, rejecting new request")
        raise HTTPException(status_code=409, detail="Indexing already in progress")

    # Validate folder paths
    valid_folders = []
    for folder_path in request.folder_paths:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            valid_folders.append(folder_path)
            logger.info(f"Valid folder: {folder_path}")
        else:
            logger.error(f"Invalid folder path: {folder_path}")

    if not valid_folders:
        raise HTTPException(status_code=400, detail="No valid folder paths provided")

    background_tasks.add_task(run_indexing, valid_folders)

    return IndexResponse(
        success=True,
        message=f"Started indexing {len(valid_folders)} folders",
        indexed_files=0
    )

@app.get("/api/index/status", response_model=IndexStatus)
async def get_index_status():
    """Get current indexing status"""
    return IndexStatus(**indexing_status)

@app.get("/api/files")
async def get_indexed_files():
    """Get list of all indexed files"""
    try:
        logger.info("Getting indexed files list...")
        files = await vector_store.get_indexed_files()
        logger.info(f"Retrieved {len(files)} indexed files")
        return {"success": True, "files": files}
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images")
async def get_indexed_images():
    """Get list of all indexed images"""
    try:
        logger.info("Getting indexed images list...")
        service = await ensure_smart_images_service()
        images = await service.get_indexed_images()
        logger.info(f"Retrieved {len(images)} indexed images")
        return {"success": True, "images": images}
    except Exception as e:
        logger.error(f"Error getting images: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/{image_id}/content")
async def get_image_content(image_id: int):
    """Return raw image bytes for display in the UI."""
    try:
        image = await vector_store.get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        file_path = image.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image file missing")

        media_type, _ = mimetypes.guess_type(file_path)
        return FileResponse(file_path, media_type=media_type or "application/octet-stream")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image content for {image_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/images/{image_id}")
async def remove_image(image_id: int):
    """Remove a single image from the index."""
    try:
        logger.info(f"Removing image with ID: {image_id}")
        await vector_store.remove_file(image_id)
        logger.info(f"Image {image_id} removed successfully")
        return {"success": True, "message": "Image removed successfully"}
    except Exception as e:
        logger.error(f"Error removing image {image_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/images/search")
async def search_images(request: SearchRequest):
    """Search for images using semantic similarity across text, tags, dates, and metadata."""
    try:
        logger.info(f"Searching images with query: '{request.query}'")
        
        # Use SmartImagesService to search
        service = await ensure_smart_images_service()
        results = await service.search_images(request.query)
        
        logger.info(f"Image search completed: {len(results)} results found")
        return {"success": True, "images": results}
    except Exception as e:
        logger.error(f"Error searching images: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=SearchResponse)
async def search_files(request: SearchRequest):
    """Search for files using semantic similarity"""
    logger.info("=" * 50)
    logger.info("SEARCH REQUEST RECEIVED")
    logger.info(f"Query: '{request.query}'")
    logger.info(f"Limit: {request.limit}, Threshold: {request.threshold}")
    logger.info("=" * 50)

    try:
        # Check if we have any indexed content
        total_files = await vector_store.get_total_indexed_files()
        total_chunks = await vector_store.get_total_chunks()

        logger.info(f"Database stats: {total_files} files, {total_chunks} chunks")

        if total_chunks == 0:
            logger.warning("No indexed content found in database")
            return SearchResponse(
                success=True,
                results=[],
                total_results=0,
                message="No indexed content found. Please add and index some folders first."
            )

        results = await vector_store.search(
            query=request.query,
            limit=request.limit or 10,
            threshold=request.threshold or 0.3
        )

        logger.info(f"Search completed: {len(results)} results found")
        for i, result in enumerate(results[:3]):
            logger.info(f"  Result {i+1}: {result['file_name']} (score: {result['similarity_score']:.3f})")

        return SearchResponse(
            success=True,
            results=results,
            total_results=len(results)
        )

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/images/search")
async def search_images_alt(request: Dict):
    """Search images by text query using CLIP embeddings."""
    try:
        search_query = request.get("query", "")
        service = await ensure_smart_images_service()
        images = await service.search_images(search_query)
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
async def query_with_llm(request: QueryRequest):
    """Query files and get AI-generated response, now with chat history."""
    logger.info("=" * 50)
    logger.info(f"QUERY REQUEST RECEIVED (Session ID: {request.session_id})")
    logger.info(f"Question: '{request.question}'")
    logger.info(f"LLM Provider: {request.llm_provider}")
    logger.info("=" * 50)

    try:
        llm_client = LLMClientFactory.create_client(request.llm_provider)
        # Store user message
        if request.session_id:
            await vector_store.add_chat_message(
                session_id=request.session_id,
                role="user",
                content=request.question
            )

        total_chunks = await vector_store.get_total_chunks()
        if total_chunks == 0:
            answer = "No indexed content found. Please add and index some folders first."
            if request.session_id:
                await vector_store.add_chat_message(request.session_id, "assistant", answer)
            return QueryResponse(success=True, answer=answer, sources=[])

        # Enhanced search logic
        logger.info("Performing vector search...")
        search_results = await vector_store.search(query=request.question, limit=15, threshold=0.2)
        if not search_results:
            logger.info("No results from initial search, trying with lower threshold...")
            search_results = await vector_store.search(query=request.question, limit=15, threshold=0.1)

        logger.info(f"Found {len(search_results)} results from vector search.")

        if not search_results:
            logger.info("No search results found, generating a general response.")
            # If no results, try a general LLM response without sources
            answer = await llm_client.generate_answer(request.question, "")
            logger.info(f"Generated general answer: {answer[:100]}...")
            if request.session_id:
                await vector_store.add_chat_message(request.session_id, "assistant", answer, sources=[])
            return QueryResponse(success=True, answer=answer, sources=[])

        # Rerank search results for relevance
        logger.info("Reranking search results...")
        reranked_results = await llm_client.rerank_results(request.question, search_results)
        logger.info(f"Reranking complete. Got {len(reranked_results)} results.")

        # Filter out irrelevant results based on reranking
        relevant_results = [result for result in reranked_results if result.get('relevance_score', 0) > 0.5]
        logger.info(f"Found {len(relevant_results)} relevant results after filtering.")

        # Limit context to top 5 results to avoid exceeding context window
        top_results = relevant_results[:5]
        logger.info(f"Using top {len(top_results)} results for context.")

        if not top_results:
            logger.info("No relevant results after reranking, generating a general response.")
            answer = await llm_client.generate_answer(request.question, "")
            logger.info(f"Generated general answer: {answer[:100]}...")
            if request.session_id:
                await vector_store.add_chat_message(request.session_id, "assistant", answer, sources=[])
            return QueryResponse(success=True, answer=answer, sources=[])

        context = "\n\n".join([f"From {result['file_name']}:\n{result['content']}" for result in top_results])
        logger.info(f"Constructed context for LLM: {context[:500]}...")

        # Include chat history for context
        history_context = ""
        if request.session_id:
            logger.info(f"Fetching chat history for session {request.session_id}...")
            messages = await vector_store.get_chat_messages(request.session_id, limit=10)
            history = [f"{msg['role']}: {msg['content']}" for msg in reversed(messages)]
            history_context = "\n".join(history)
            logger.info("Chat history fetched.")

        full_context = f"Previous conversation:\n{history_context}\n\nFile context:\n{context}"
        logger.info("Generating final answer with LLM...")

        answer = await llm_client.generate_answer(request.question, full_context)
        logger.info(f"LLM generated answer: {answer[:100]}...")

        sources = list({
            result["file_path"]: {
                "file_path": result["file_path"],
                "content_preview": result["content"][:300] + "...",
                "similarity_score": result["similarity_score"]
            }
            for result in search_results
        }.values())
        logger.info(f"Constructed {len(sources)} sources for response.")

        # Store assistant message
        if request.session_id:
            logger.info("Storing assistant message in chat history...")
            await vector_store.add_chat_message(
                session_id=request.session_id,
                role="assistant",
                content=answer,
                sources=sources
            )
            logger.info("Assistant message stored.")

        logger.info("Query processed successfully.")
        return QueryResponse(success=True, answer=answer, sources=sources)

    except Exception as e:
        logger.error(f"Query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/api/images/rename")
async def rename_image(request: Dict):
    """Rename an image with a new semantic name."""
    try:
        image_id = request.get("image_id")
        new_name = request.get("new_name")
        result = await smart_images_service.rename_image(image_id, new_name)
        return {"success": True, "message": "Image renamed successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New File Organiser Endpoints

@app.get("/api/folders/hierarchy")
async def get_folder_hierarchy(root_id: Optional[int] = None):
    """Get folder hierarchy for the file organiser"""
    try:
        logger.info(f"Getting folder hierarchy (root_id: {root_id})")
        hierarchy = await vector_store.get_folder_hierarchy(root_id)
        logger.info(f"Retrieved hierarchy with {len(hierarchy)} root folders")
        return {"success": True, "hierarchy": hierarchy}
    except Exception as e:
        logger.error(f"Error getting folder hierarchy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/organise/analyze")
async def analyze_folder_for_organisation(request: OrganiseRequest):
    """Analyze a folder for organization opportunities"""
    try:
        logger.info(f"Analyzing folder {request.folder_id} for organization")
        organiser = await ensure_file_organiser()

        result = await organiser.analyze_folder_for_organisation(
            request.folder_id,
            request.dry_run
        )

        return result

    except Exception as e:
        logger.error(f"Error analyzing folder for organization: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/organise/execute")
async def execute_organisation(request: ExecuteOrganiseRequest):
    """Execute file organization based on analysis"""
    try:
        logger.info(f"Executing organization for folder {request.folder_id}")
        organiser = await ensure_file_organiser()

        result = await organiser.execute_organisation(
            request.folder_id,
            request.actions,
            request.confirm
        )

        return result

    except Exception as e:
        logger.error(f"Error executing organization: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/folders/{folder_id}/files")
async def get_folder_files(folder_id: int, recursive: bool = False):
    """Get files in a specific folder"""
    try:
        logger.info(f"Getting files for folder {folder_id} (recursive: {recursive})")

        if recursive:
            files = await vector_store.get_files_in_folder_recursive(folder_id)
        else:
            # Get files only in this folder (not implemented yet, using recursive for now)
            files = await vector_store.get_files_in_folder_recursive(folder_id)

        logger.info(f"Retrieved {len(files)} files")
        return {"success": True, "files": files}

    except Exception as e:
        logger.error(f"Error getting folder files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat History Endpoints

@app.post("/api/chat/sessions", response_model=ChatSession)
async def create_chat_session(request: CreateChatSessionRequest):
    """Create a new chat session"""
    try:
        session = await vector_store.create_chat_session(request.session_name)
        return session
    except Exception as e:
        logger.error(f"Error creating chat session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create chat session")

@app.get("/api/chat/sessions", response_model=List[ChatSession])
async def get_chat_sessions():
    """Get all chat sessions"""
    try:
        sessions = await vector_store.get_chat_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Error getting chat sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get chat sessions")

@app.get("/api/chat/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_chat_messages(session_id: int):
    """Get messages for a specific chat session"""
    try:
        messages = await vector_store.get_chat_messages(session_id)
        return messages
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get chat messages")

@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: int):
    """Delete a chat session"""
    try:
        await vector_store.delete_chat_session(session_id)
        return {"success": True, "message": "Chat session deleted"}
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete chat session")

@app.post("/api/chat/generate-name")
async def generate_chat_name(request: GenerateChatNameRequest):
    """Generate a name for a chat session"""
    try:
        llm_client_instance = LLMClientFactory.create_client(request.llm_provider)
        session_name = await llm_client_instance.generate_session_name(request.message)
        await vector_store.update_chat_session_name(request.session_id, session_name)
        return {"success": True, "session_name": session_name}
    except Exception as e:
        logger.error(f"Error generating chat name: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate chat name")

# Existing endpoints continue...

@app.get("/api/folders", response_model=List[FolderInfo])
async def get_indexed_folders():
    """Get list of currently indexed folders"""
    try:
        logger.info("Getting indexed folders list...")
        folders = await vector_store.get_indexed_folders()
        logger.info(f"Retrieved {len(folders)} indexed folders")
        return folders
    except Exception as e:
        logger.error(f"Error getting folders: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/folders/{folder_id}")
async def remove_folder(folder_id: int):
    """Remove a folder from the index"""
    try:
        logger.info(f"Removing folder with ID: {folder_id}")
        await vector_store.remove_folder(folder_id)
        logger.info(f"Folder {folder_id} removed successfully")
        return {"success": True, "message": "Folder removed successfully"}
    except Exception as e:
        logger.error(f"Error removing folder {folder_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/index/clear")
async def clear_index():
    """Clear the entire index"""
    try:
        logger.info("Clearing entire index...")
        await vector_store.clear_all()
        logger.info("Index cleared successfully")
        return {"success": True, "message": "Index cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing index: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Add debug endpoint
@app.get("/api/debug/stats")
async def get_debug_stats():
    """Get detailed debug statistics"""
    try:
        stats = await vector_store.get_debug_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting debug stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_indexing(folder_paths: List[str]):
    """Background task to run file indexing"""
    global indexing_status

    indexing_status["is_indexing"] = True
    indexing_status["progress"] = 0
    indexing_status["processed_files"] = 0
    indexing_status["total_files"] = 0

    try:
        logger.info("Starting indexing process...")

        # Count total files first
        total_files = 0
        for folder_path in folder_paths:
            count = await file_indexer.count_files(folder_path)
            total_files += count
            logger.info(f"Found {count} supported files in {folder_path}")

        indexing_status["total_files"] = total_files
        logger.info(f"Total files to process: {total_files}")

        if total_files == 0:
            logger.warning("No supported files found in any folder")
            return

        processed_files = 0

        # Index each folder
        for folder_path in folder_paths:
            logger.info(f"Processing folder: {folder_path}")
            async for file_path, progress in file_indexer.index_folder(folder_path):
                processed_files += 1
                indexing_status["current_file"] = str(file_path)
                indexing_status["processed_files"] = processed_files
                indexing_status["progress"] = int((processed_files / total_files) * 100) if total_files > 0 else 100

                if processed_files % 10 == 0:
                    logger.info(f"Progress: {processed_files}/{total_files} files processed ({indexing_status['progress']}%)")

        indexing_status["progress"] = 100
        logger.info(f"Indexing completed successfully! Processed {processed_files} files.")

        # Log final stats
        final_stats = await vector_store.get_debug_stats()
        logger.info(f"Final database stats: {final_stats}")

    except Exception as e:
        logger.error(f"Indexing error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        indexing_status["is_indexing"] = False
        indexing_status["current_file"] = ""

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions"""
    logger.critical(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.post("/api/settings/api-key")
async def save_api_key(api_key: ApiKey):
    """Save API key to local storage"""
    try:
        config_file = os.path.expanduser("~/.smartfile_ai_config.json")
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    config = {}  # File is empty or corrupt, start fresh

        config['gemini_api_key'] = api_key.key

        with open(config_file, 'w') as f:
            json.dump(config, f)

        # Re-initialize the LLM client to use the new key
        global llm_client
        llm_client = LLMClientFactory.create_client()

        return {"success": True, "message": "API key saved successfully"}
    except Exception as e:
        logger.error(f"Error saving API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save API key")

@app.get("/api/settings/api-key", response_model=ApiKey)
async def get_api_key():
    """Get API key from local storage"""
    try:
        config_file = os.path.expanduser("~/.smartfile_ai_config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                try:
                    config = json.load(f)
                    return ApiKey(key=config.get('gemini_api_key', ''))
                except json.JSONDecodeError:
                    return ApiKey(key='')  # File is empty or corrupt
        return ApiKey(key='')
    except Exception as e:
        logger.error(f"Error getting API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get API key")

def find_free_port(start_port: int = 8000) -> int:
    """Find a free port starting from the given port"""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                port += 1
                if port > start_port + 100:
                    raise RuntimeError(f"Could not find a free port starting from {start_port}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SmartFile AI Backend Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", type=str, default="info", choices=["debug", "info", "warning", "error"], help="Log level")

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

    try:
        logger.info(f"Starting SmartFile AI Backend on {args.host}:{args.port}")
        uvicorn.run(
            "main:app" if args.reload else app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except OSError as e:
        if "Address already in use" in str(e):
            try:
                free_port = find_free_port(args.port + 1)
                logger.info(f"Port {args.port} is busy, using port {free_port} instead")
                uvicorn.run(
                    "main:app" if args.reload else app,
                    host=args.host,
                    port=free_port,
                    reload=args.reload,
                    log_level=args.log_level
                )
            except Exception as fallback_error:
                logger.error(f"Failed to start server on alternative port: {fallback_error}")
                sys.exit(1)
        else:
            logger.error(f"Failed to start server: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
