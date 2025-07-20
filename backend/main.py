# #backend\main.py
# import asyncio
# import os
# import sys
# from pathlib import Path
# from typing import List, Optional, Dict, Any
# import uvicorn
# from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# import logging
# import argparse
# import socket
# from contextlib import asynccontextmanager
#
# # Configure logging with more detail
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)
#
# # Add backend directory to Python path
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#
# from services.indexer import FileIndexer
# from services.vector_store import VectorStore
# from services.llm_client import LLMClientFactory
# from models.schemas import (
#     IndexRequest, SearchRequest, QueryRequest,
#     IndexResponse, SearchResponse, QueryResponse,
#     FolderInfo, IndexStatus
# )
#
# # Global services
# vector_store = None
# file_indexer = None
# llm_client = None
# indexing_status = {"is_indexing": False, "progress": 0, "current_file": ""}
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Application lifespan manager for startup and shutdown"""
#     global vector_store, file_indexer, llm_client
#
#     # Startup
#     try:
#         logger.info("Initializing SmartFile AI Backend...")
#         vector_store = VectorStore()
#         await vector_store.initialize()
#         file_indexer = FileIndexer(vector_store)
#         llm_client = LLMClientFactory.create_client()
#         logger.info("Backend started successfully")
#         yield
#     except Exception as e:
#         logger.error(f"Initialization failed: {str(e)}")
#         raise
#     finally:
#         # Shutdown
#         logger.info("Shutting down SmartFile AI Backend...")
#         try:
#             if vector_store:
#                 await vector_store.close()
#         except Exception as e:
#             logger.error(f"Error during shutdown: {str(e)}")
#
# # Create FastAPI app with lifespan
# app = FastAPI(
#     title="SmartFile AI Backend",
#     version="1.0.0",
#     lifespan=lifespan,
#     description="AI-powered file indexing and search backend"
# )
#
# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",  # Next.js
#         "http://127.0.0.1:3000",  # Next.js alternative
#         "app://*",                # Packaged Electron
#         "file://*"                # Local file access
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {"message": "SmartFile AI Backend is running", "version": "1.0.0"}
#
# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     try:
#         # Check if services are initialized
#         services_status = {
#             "vector_store": vector_store is not None,
#             "file_indexer": file_indexer is not None,
#             "llm_client": llm_client is not None
#         }
#
#         return {
#             "status": "healthy",
#             "version": "1.0.0",
#             "services": services_status
#         }
#     except Exception as e:
#         logger.error(f"Health check error: {str(e)}")
#         raise HTTPException(status_code=503, detail="Service unhealthy")
#
# @app.post("/api/index", response_model=IndexResponse)
# async def index_folders(request: IndexRequest, background_tasks: BackgroundTasks):
#     """Index the specified folders"""
#     try:
#         logger.info(f"Received index request for folders: {request.folder_paths}")
#
#         if not request.folder_paths:
#             raise HTTPException(status_code=400, detail="No folder paths provided")
#
#         if indexing_status["is_indexing"]:
#             raise HTTPException(status_code=409, detail="Indexing already in progress")
#
#         # Validate folder paths exist
#         invalid_paths = []
#         for folder_path in request.folder_paths:
#             if not os.path.exists(folder_path):
#                 invalid_paths.append(folder_path)
#
#         if invalid_paths:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid folder paths: {', '.join(invalid_paths)}"
#             )
#
#         background_tasks.add_task(run_indexing, request.folder_paths)
#
#         return IndexResponse(
#             success=True,
#             message=f"Started indexing {len(request.folder_paths)} folders",
#             indexed_files=0
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Index request error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to start indexing: {str(e)}")
#
# @app.get("/api/index/status", response_model=IndexStatus)
# async def get_index_status():
#     """Get current indexing status"""
#     try:
#         return IndexStatus(**indexing_status)
#     except Exception as e:
#         logger.error(f"Status request error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to get indexing status")
#
# @app.post("/api/search", response_model=SearchResponse)
# async def search_files(request: SearchRequest):
#     """Search for files using semantic similarity"""
#     try:
#         logger.info(f"Search request: {request.query}")
#
#         if not request.query or not request.query.strip():
#             raise HTTPException(status_code=400, detail="Search query cannot be empty")
#
#         if not vector_store:
#             raise HTTPException(status_code=503, detail="Vector store not initialized")
#
#         results = await vector_store.search(
#             query=request.query.strip(),
#             limit=request.limit or 10,
#             threshold=request.threshold or 0.5
#         )
#
#         logger.info(f"Search returned {len(results)} results")
#
#         return SearchResponse(
#             success=True,
#             results=results,
#             total_results=len(results)
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Search error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
#
# @app.post("/api/query", response_model=QueryResponse)
# async def query_with_llm(request: QueryRequest):
#     """Query files and get AI-generated response"""
#     try:
#         logger.info(f"Query request: {request.question}")
#
#         if not request.question or not request.question.strip():
#             raise HTTPException(status_code=400, detail="Question cannot be empty")
#
#         if not vector_store:
#             raise HTTPException(status_code=503, detail="Vector store not initialized")
#
#         if not llm_client:
#             raise HTTPException(status_code=503, detail="LLM client not initialized")
#
#         # First, search for relevant content
#         search_results = await vector_store.search(
#             query=request.question.strip(),
#             limit=5,
#             threshold=0.3
#         )
#
#         logger.info(f"Found {len(search_results)} relevant documents")
#
#         if not search_results:
#             return QueryResponse(
#                 success=True,
#                 answer="I couldn't find any relevant information in your files to answer this question. Please make sure your folders are indexed and contain relevant content.",
#                 sources=[]
#             )
#
#         # Generate answer using LLM
#         context = "\n\n".join([result["content"] for result in search_results])
#         answer = await llm_client.generate_answer(request.question.strip(), context)
#
#         sources = [
#             {
#                 "file_path": result["file_path"],
#                 "content_preview": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
#                 "similarity_score": result["similarity_score"]
#             }
#             for result in search_results
#         ]
#
#         return QueryResponse(
#             success=True,
#             answer=answer,
#             sources=sources
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Query error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
#
# @app.get("/api/files")
# async def get_indexed_files():
#     """Get list of all indexed files"""
#     try:
#         if not vector_store:
#             raise HTTPException(status_code=503, detail="Vector store not initialized")
#
#         files = await vector_store.get_indexed_files()
#         return {"success": True, "files": files}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting files: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to get files: {str(e)}")
#
# @app.get("/api/folders", response_model=List[FolderInfo])
# async def get_indexed_folders():
#     """Get list of currently indexed folders"""
#     try:
#         if not vector_store:
#             raise HTTPException(status_code=503, detail="Vector store not initialized")
#
#         folders = await vector_store.get_indexed_folders()
#         logger.info(f"Retrieved {len(folders)} indexed folders")
#         return folders
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting folders: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to get folders: {str(e)}")
#
# @app.delete("/api/folders/{folder_id}")
# async def remove_folder(folder_id: int):
#     """Remove a folder from the index"""
#     try:
#         if not vector_store:
#             raise HTTPException(status_code=503, detail="Vector store not initialized")
#
#         if folder_id < 0:
#             raise HTTPException(status_code=400, detail="Invalid folder ID")
#
#         await vector_store.remove_folder(folder_id)
#         return {"success": True, "message": "Folder removed successfully"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error removing folder: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to remove folder: {str(e)}")
#
# @app.delete("/api/index/clear")
# async def clear_index():
#     """Clear the entire index"""
#     try:
#         if not vector_store:
#             raise HTTPException(status_code=503, detail="Vector store not initialized")
#
#         await vector_store.clear_all()
#
#         # Reset indexing status
#         global indexing_status
#         indexing_status = {"is_indexing": False, "progress": 0, "current_file": ""}
#
#         return {"success": True, "message": "Index cleared successfully"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error clearing index: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to clear index: {str(e)}")
#
# async def run_indexing(folder_paths: List[str]):
#     """Background task to run file indexing"""
#     global indexing_status
#
#     indexing_status["is_indexing"] = True
#     indexing_status["progress"] = 0
#     indexing_status["current_file"] = ""
#
#     try:
#         total_files = 0
#         processed_files = 0
#
#         logger.info("Starting indexing process...")
#
#         # Count total files first
#         for folder_path in folder_paths:
#             try:
#                 count = await file_indexer.count_files(folder_path)
#                 total_files += count
#                 logger.info(f"Found {count} files in {folder_path}")
#             except Exception as e:
#                 logger.error(f"Error counting files in {folder_path}: {str(e)}")
#                 continue
#
#         logger.info(f"Total files to process: {total_files}")
#
#         if total_files == 0:
#             logger.warning("No files found to index")
#             return
#
#         # Index each folder
#         for folder_path in folder_paths:
#             try:
#                 logger.info(f"Indexing folder: {folder_path}")
#                 async for file_path, progress in file_indexer.index_folder(folder_path):
#                     processed_files += 1
#                     indexing_status["current_file"] = str(file_path)
#                     indexing_status["progress"] = int((processed_files / total_files) * 100) if total_files > 0 else 100
#                     logger.info(f"Processed {processed_files}/{total_files}: {file_path}")
#             except Exception as e:
#                 logger.error(f"Error indexing folder {folder_path}: {str(e)}")
#                 continue
#
#         indexing_status["progress"] = 100
#         logger.info(f"Indexing completed. Processed {processed_files} files.")
#
#     except Exception as e:
#         logger.error(f"Indexing error: {str(e)}")
#     finally:
#         indexing_status["is_indexing"] = False
#         indexing_status["current_file"] = ""
#
# # Exception handlers
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     """Handle HTTP exceptions"""
#     logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail}
#     )
#
# @app.exception_handler(Exception)
# async def generic_exception_handler(request: Request, exc: Exception):
#     """Handle generic exceptions"""
#     logger.critical(f"Unhandled error: {str(exc)}")
#     return JSONResponse(
#         status_code=500,
#         content={"detail": "Internal server error"}
#     )
#
# def find_free_port(start_port: int = 8000) -> int:
#     """Find a free port starting from the given port"""
#     port = start_port
#     while True:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             try:
#                 s.bind(('127.0.0.1', port))
#                 return port
#             except OSError:
#                 port += 1
#                 if port > start_port + 100:  # Prevent infinite loop
#                     raise RuntimeError(f"Could not find a free port starting from {start_port}")
#
# def main():
#     """Main entry point"""
#     parser = argparse.ArgumentParser(description="SmartFile AI Backend Server")
#     parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
#     parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to")
#     parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
#     parser.add_argument("--log-level", type=str, default="info", choices=["debug", "info", "warning", "error"], help="Log level")
#
#     args = parser.parse_args()
#
#     # Set log level
#     logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
#
#     try:
#         logger.info(f"Starting SmartFile AI Backend on {args.host}:{args.port}")
#         uvicorn.run(
#             "main:app" if args.reload else app,
#             host=args.host,
#             port=args.port,
#             reload=args.reload,
#             log_level=args.log_level
#         )
#     except OSError as e:
#         if "Address already in use" in str(e):
#             try:
#                 free_port = find_free_port(args.port + 1)
#                 logger.info(f"Port {args.port} is busy, using port {free_port} instead")
#                 uvicorn.run(
#                     "main:app" if args.reload else app,
#                     host=args.host,
#                     port=free_port,
#                     reload=args.reload,
#                     log_level=args.log_level
#                 )
#             except Exception as fallback_error:
#                 logger.error(f"Failed to start server on alternative port: {fallback_error}")
#                 sys.exit(1)
#         else:
#             logger.error(f"Failed to start server: {e}")
#             sys.exit(1)
#     except KeyboardInterrupt:
#         logger.info("Server shutdown requested")
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         sys.exit(1)
#
# if __name__ == "__main__":
#     main()


import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import traceback

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('smartfile_ai.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.indexer import FileIndexer
from services.vector_store import VectorStore
from services.llm_client import LLMClientFactory
from models.schemas import (
    IndexRequest, SearchRequest, QueryRequest,
    IndexResponse, SearchResponse, QueryResponse,
    FolderInfo, IndexStatus
)

app = FastAPI(title="SmartFile AI Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
vector_store = None
file_indexer = None
llm_client = None
indexing_status = {"is_indexing": False, "progress": 0, "current_file": "", "total_files": 0, "processed_files": 0}

@app.on_event("startup")
async def startup_event():
    global vector_store, file_indexer, llm_client

    try:
        logger.info("=" * 50)
        logger.info("STARTING SMARTFILE AI BACKEND")
        logger.info("=" * 50)

        # Initialize services
        logger.info("Initializing vector store...")
        vector_store = VectorStore()
        await vector_store.initialize()
        logger.info("Vector store initialized successfully")

        logger.info("Initializing file indexer...")
        file_indexer = FileIndexer(vector_store)
        logger.info("File indexer initialized successfully")

        logger.info("Initializing LLM client...")
        llm_client = LLMClientFactory.create_client()
        logger.info("LLM client initialized successfully")

        # Check database status
        folders = await vector_store.get_indexed_folders()
        files = await vector_store.get_indexed_files()
        logger.info(f"Database status: {len(folders)} folders, {len(files)} files indexed")

        logger.info("SmartFile AI Backend started successfully!")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Failed to initialize backend: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

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

@app.post("/api/index", response_model=IndexResponse)
async def index_folders(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index the specified folders"""
    logger.info("=" * 50)
    logger.info("INDEXING REQUEST RECEIVED")
    logger.info(f"Folders to index: {request.folder_paths}")
    logger.info("=" * 50)

    if indexing_status["is_indexing"]:
        logger.warning("⚠️ Indexing already in progress, rejecting new request")
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
            logger.warning("⚠️ No indexed content found in database")
            return SearchResponse(
                success=True,
                results=[],
                total_results=0,
                message="No indexed content found. Please add and index some folders first."
            )

        results = await vector_store.search(
            query=request.query,
            limit=request.limit or 10,
            threshold=request.threshold or 0.3  # Very low threshold for better results
        )

        logger.info(f"Search completed: {len(results)} results found")
        for i, result in enumerate(results[:3]):  # Log first 3 results
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

@app.post("/api/query", response_model=QueryResponse)
async def query_with_llm(request: QueryRequest):
    """Query files and get AI-generated response"""
    logger.info("=" * 50)
    logger.info("QUERY REQUEST RECEIVED")
    logger.info(f"Question: '{request.question}'")
    logger.info("=" * 50)

    try:
        # Check if we have any indexed content
        total_files = await vector_store.get_total_indexed_files()
        total_chunks = await vector_store.get_total_chunks()

        logger.info(f"Database stats: {total_files} files, {total_chunks} chunks")

        if total_chunks == 0:
            logger.warning("⚠️ No indexed content found for query")
            return QueryResponse(
                success=True,
                answer="No indexed content found. Please add and index some folders first, then try your question again.",
                sources=[]
            )

        # Search for relevant content with very low threshold
        logger.info("🔍 Searching for relevant content...")
        search_results = await vector_store.search(
            query=request.question,
            limit=10,
            threshold=0.1  # Very low threshold for queries
        )

        logger.info(f"📋 Found {len(search_results)} relevant documents")

        if not search_results:
            # Try a broader search with even lower threshold
            logger.info("🔍 Trying broader search with lower threshold...")
            search_results = await vector_store.search(
                query=request.question,
                limit=10,
                threshold=0.05
            )
            logger.info(f"📋 Broader search found {len(search_results)} documents")

        if not search_results:
            logger.warning("⚠️ No relevant content found for query")
            return QueryResponse(
                success=True,
                answer=f"I couldn't find any content related to '{request.question}' in your indexed files. This could mean:\n\n1. The content doesn't exist in your files\n2. The files haven't been indexed yet\n3. The content is in a format that wasn't processed\n\nTry checking the 'Browse Files' section to see what content has been indexed.",
                sources=[]
            )

        # Log the search results
        for i, result in enumerate(search_results):
            logger.info(f"  Result {i+1}: {result['file_name']} (score: {result['similarity_score']:.3f})")
            logger.debug(f"    Content preview: {result['content'][:100]}...")

        # Generate answer using LLM
        logger.info("Generating AI response...")
        context = "\n\n".join([f"From {result['file_name']}:\n{result['content']}" for result in search_results])
        answer = await llm_client.generate_answer(request.question, context)

        logger.info("AI response generated successfully")

        sources = [
            {
                "file_path": result["file_path"],
                "content_preview": result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"],
                "similarity_score": result["similarity_score"]
            }
            for result in search_results
        ]

        return QueryResponse(
            success=True,
            answer=answer,
            sources=sources
        )

    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

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
            logger.warning("⚠️ No supported files found in any folder")
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

                if processed_files % 10 == 0:  # Log every 10 files
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False
    )
