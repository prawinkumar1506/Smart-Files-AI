import os
import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, db_path: str = "smartfile_ai.db"):
        self.db_path = db_path
        self.connection = None

    async def initialize(self):
        """Initialize the SQLite database with vector support"""
        try:
            logger.info(f"Initializing database at: {os.path.abspath(self.db_path)}")
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            # Ensure foreign keys are enabled immediately after connection
            self.connection.execute("PRAGMA foreign_keys = ON")

            # Create tables
            await self._create_tables()

            # Log initial stats
            stats = await self.get_debug_stats()
            logger.info(f"Database initialized with stats: {stats}")

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def _create_tables(self):
        """Create necessary database tables"""
        cursor = self.connection.cursor()

        try:
            logger.info("Creating database tables...")

            # Folders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_count INTEGER DEFAULT 0
                )
            """)

            # Files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id INTEGER,
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER,
                    last_modified TIMESTAMP,
                    content_hash TEXT,
                    FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE CASCADE
                )
            """)

            # Document chunks table (stores text chunks and their embeddings)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER,
                    chunk_index INTEGER,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
                )
            """)

            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_file ON document_chunks(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path)")

            self.connection.commit()
            logger.info("Database tables created successfully")

        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def get_debug_stats(self) -> Dict[str, Any]:
        """Get detailed debug statistics"""
        cursor = self.connection.cursor()

        try:
            # Count folders
            cursor.execute("SELECT COUNT(*) as count FROM folders")
            folder_count = cursor.fetchone()['count']

            # Count files
            cursor.execute("SELECT COUNT(*) as count FROM files")
            file_count = cursor.fetchone()['count']

            # Count chunks
            cursor.execute("SELECT COUNT(*) as count FROM document_chunks")
            chunk_count = cursor.fetchone()['count']

            # Get file types
            cursor.execute("SELECT file_type, COUNT(*) as count FROM files GROUP BY file_type")
            file_types = {row['file_type']: row['count'] for row in cursor.fetchall()}

            # Get recent files
            cursor.execute("SELECT file_name, file_path FROM files ORDER BY id DESC LIMIT 5")
            recent_files = [{'name': row['file_name'], 'path': row['file_path']} for row in cursor.fetchall()]

            return {
                'folders': folder_count,
                'files': file_count,
                'chunks': chunk_count,
                'file_types': file_types,
                'recent_files': recent_files,
                'database_path': os.path.abspath(self.db_path)
            }

        except Exception as e:
            logger.error(f"Error getting debug stats: {str(e)}")
            return {'error': str(e)}

    async def get_total_indexed_files(self) -> int:
        """Get total number of indexed files"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM files")
        return cursor.fetchone()['count']

    async def get_total_chunks(self) -> int:
        """Get total number of document chunks"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM document_chunks")
        return cursor.fetchone()['count']

    async def add_folder(self, folder_path: str) -> int:
        """Add a folder to the database"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO folders (path, last_indexed) VALUES (?, ?)",
                (folder_path, datetime.now())
            )
            self.connection.commit()
            folder_id = cursor.lastrowid
            logger.info(f"Added folder to database: {folder_path} (ID: {folder_id})")
            return folder_id
        except Exception as e:
            logger.error(f"Error adding folder {folder_path}: {str(e)}")
            raise

    async def add_file(self, folder_id: int, file_path: str, file_info: Dict[str, Any]) -> int:
        """Add a file to the database"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO files 
                (folder_id, file_path, file_name, file_type, file_size, last_modified, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                folder_id,
                file_path,
                file_info.get('name', Path(file_path).name),
                file_info.get('type', Path(file_path).suffix),
                file_info.get('size', 0),
                file_info.get('modified', datetime.now()),
                file_info.get('hash', '')
            ))
            self.connection.commit()
            file_id = cursor.lastrowid
            logger.debug(f"Added file to database: {file_info.get('name')} (ID: {file_id})")
            return file_id
        except Exception as e:
            logger.error(f"Error adding file {file_path}: {str(e)}")
            raise

    async def add_document_chunk(self, file_id: int, chunk_index: int, content: str, embedding: np.ndarray):
        """Add a document chunk with its embedding"""
        cursor = self.connection.cursor()

        try:
            # Convert numpy array to bytes for storage
            embedding_bytes = embedding.astype(np.float32).tobytes()

            cursor.execute("""
                INSERT INTO document_chunks (file_id, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?)
            """, (file_id, chunk_index, content, embedding_bytes))

            self.connection.commit()
            logger.debug(f"Added chunk {chunk_index} for file {file_id} (content length: {len(content)})")

        except Exception as e:
            logger.error(f"Error adding document chunk: {str(e)}")
            raise

    async def search(self, query: str, limit: int = 10, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search for similar document chunks using cosine similarity"""
        try:
            logger.info(f"Starting search for: '{query}' (threshold: {threshold}, limit: {limit})")

            from .embedding_service import EmbeddingService

            # Generate embedding for the query
            embedding_service = EmbeddingService()
            query_embedding = await embedding_service.generate_embedding(query)
            logger.debug(f"Generated query embedding with shape: {query_embedding.shape}")

            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    dc.content,
                    dc.embedding,
                    f.file_path,
                    f.file_name,
                    f.file_type,
                    f.last_modified
                FROM document_chunks dc
                JOIN files f ON dc.file_id = f.id
            """)

            results = []
            query_embedding_norm = np.linalg.norm(query_embedding)

            rows = cursor.fetchall()
            logger.info(f"Searching through {len(rows)} document chunks")

            if len(rows) == 0:
                logger.warning("No document chunks found in database")
                return []

            similarities_calculated = 0

            for row in rows:
                try:
                    # Convert bytes back to numpy array
                    stored_embedding = np.frombuffer(row['embedding'], dtype=np.float32)

                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, stored_embedding) / (
                            query_embedding_norm * np.linalg.norm(stored_embedding)
                    )

                    similarities_calculated += 1

                    if similarity >= threshold:
                        results.append({
                            'content': row['content'],
                            'file_path': row['file_path'],
                            'file_name': row['file_name'],
                            'file_type': row['file_type'],
                            'last_modified': row['last_modified'],
                            'similarity_score': float(similarity)
                        })

                        logger.debug(f"Match found: {row['file_name']} (similarity: {similarity:.3f})")

                except Exception as e:
                    logger.error(f"Error processing search result: {str(e)}")
                    continue

            # Sort by similarity score and return top results
            results.sort(key=lambda x: x['similarity_score'], reverse=True)

            logger.info(f"Search completed: {similarities_calculated} similarities calculated, {len(results)} results above threshold")

            if len(results) == 0:
                logger.warning(f"No results found above threshold {threshold}")
                # Log some sample similarities for debugging
                sample_similarities = []
                cursor.execute("SELECT content FROM document_chunks LIMIT 3")
                sample_rows = cursor.fetchall()
                for row in sample_rows:
                    try:
                        stored_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                        similarity = np.dot(query_embedding, stored_embedding) / (
                                query_embedding_norm * np.linalg.norm(stored_embedding)
                        )
                        sample_similarities.append(similarity)
                    except:
                        pass
                logger.info(f"Sample similarities: {sample_similarities}")

            return results[:limit]

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def get_indexed_files(self) -> List[Dict[str, Any]]:
        """Get list of all indexed files"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT 
                    f.id,
                    f.file_path,
                    f.file_name,
                    f.file_type,
                    f.file_size,
                    f.last_modified,
                    fo.path as folder_path,
                    COUNT(dc.id) as chunk_count
                FROM files f
                JOIN folders fo ON f.folder_id = fo.id
                LEFT JOIN document_chunks dc ON f.id = dc.file_id
                GROUP BY f.id, f.file_path, f.file_name, f.file_type, f.file_size, f.last_modified, fo.path
                ORDER BY f.file_name
            """)

            files = [
                {
                    'id': row['id'],
                    'file_path': row['file_path'],
                    'file_name': row['file_name'],
                    'file_type': row['file_type'],
                    'file_size': row['file_size'],
                    'last_modified': row['last_modified'],
                    'folder_path': row['folder_path'],
                    'chunk_count': row['chunk_count']
                }
                for row in cursor.fetchall()
            ]

            logger.info(f"Retrieved {len(files)} indexed files")
            return files

        except Exception as e:
            logger.error(f"Error getting indexed files: {str(e)}")
            raise

    async def get_indexed_folders(self) -> List[Dict[str, Any]]:
        """Get list of indexed folders"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT 
                    f.id,
                    f.path,
                    f.last_indexed,
                    COUNT(files.id) as file_count
                FROM folders f
                LEFT JOIN files ON f.id = files.folder_id
                GROUP BY f.id, f.path, f.last_indexed
                ORDER BY f.last_indexed DESC
            """)

            folders = [
                {
                    'id': row['id'],
                    'path': row['path'],
                    'file_count': row['file_count'],
                    'last_indexed': row['last_indexed']
                }
                for row in cursor.fetchall()
            ]

            logger.info(f"Retrieved {len(folders)} indexed folders")
            return folders

        except Exception as e:
            logger.error(f"Error getting indexed folders: {str(e)}")
            raise

    async def remove_folder(self, folder_id: int):
        """Remove a folder and all its associated data"""
        cursor = self.connection.cursor()
        try:
            # Get folder info before deletion
            cursor.execute("SELECT path FROM folders WHERE id = ?", (folder_id,))
            folder = cursor.fetchone()

            if folder:
                logger.info(f"Removing folder: {folder['path']} (ID: {folder_id})")
                cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
                self.connection.commit()
                logger.info(f"Folder and all associated files/chunks removed successfully")
            else:
                logger.warning(f"Folder with ID {folder_id} not found")

        except Exception as e:
            logger.error(f"Error removing folder {folder_id}: {str(e)}")
            raise

    async def clear_all(self):
        """Clear all data from the database"""
        cursor = self.connection.cursor()
        try:
            logger.info("Clearing all data from database...")
            cursor.execute("DELETE FROM document_chunks")
            cursor.execute("DELETE FROM files")
            cursor.execute("DELETE FROM folders")
            self.connection.commit()
            logger.info("All data cleared from database")
        except Exception as e:
            logger.error(f"Error clearing database: {str(e)}")
            raise

    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
