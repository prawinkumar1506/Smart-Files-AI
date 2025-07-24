import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
import traceback
import os

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
            
            # Enable foreign keys
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
            
            # Migration logic for the folders table
            try:
                cursor.execute("PRAGMA table_info(folders)")
                columns = [column['name'] for column in cursor.fetchall()]
                
                if 'parent_id' not in columns:
                    logger.info("Migrating folders table: adding parent_id and level columns")
                    cursor.execute("ALTER TABLE folders ADD COLUMN parent_id INTEGER REFERENCES folders(id) ON DELETE CASCADE")
                    cursor.execute("ALTER TABLE folders ADD COLUMN level INTEGER DEFAULT 0")
                
                if 'name' not in columns:
                    logger.info("Migrating folders table: adding name column")
                    cursor.execute("ALTER TABLE folders ADD COLUMN name TEXT NOT NULL DEFAULT ''")

                self.connection.commit()
            except sqlite3.OperationalError as e:
                # This is expected if the table doesn't exist yet.
                if "no such table" not in str(e).lower():
                    raise

            # Updated Folders table with hierarchy support
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    level INTEGER DEFAULT 0,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_count INTEGER DEFAULT 0,
                    FOREIGN KEY (parent_id) REFERENCES folders (id) ON DELETE CASCADE
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
            
            # New table for file classifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER,
                    classification TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
                )
            """)
            
            # New table for organization actions (for rollback capability)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organisation_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id INTEGER,
                    action_type TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    classification TEXT,
                    confidence REAL,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_file ON document_chunks(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_folders_parent ON folders(parent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_classifications_file ON file_classifications(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_folder ON organisation_actions(folder_id)")
            
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
    
    async def add_folder(self, folder_path: str, parent_id: Optional[int] = None) -> int:
        """Add a folder to the database with hierarchy support"""
        cursor = self.connection.cursor()
        try:
            folder_name = Path(folder_path).name
            level = 0
            
            if parent_id:
                # Get parent level
                cursor.execute("SELECT level FROM folders WHERE id = ?", (parent_id,))
                parent = cursor.fetchone()
                if parent:
                    level = parent['level'] + 1
            
            cursor.execute(
                "INSERT OR REPLACE INTO folders (path, name, parent_id, level, last_indexed) VALUES (?, ?, ?, ?, ?)",
                (folder_path, folder_name, parent_id, level, datetime.now())
            )
            self.connection.commit()
            folder_id = cursor.lastrowid
            logger.info(f"Added folder to database: {folder_path} (ID: {folder_id}, Level: {level})")
            return folder_id
        except Exception as e:
            logger.error(f"Error adding folder {folder_path}: {str(e)}")
            raise
    
    async def add_subfolder(self, parent_id: int, folder_path: str, folder_name: str) -> int:
        """Add a subfolder under a parent folder"""
        return await self.add_folder(folder_path, parent_id)
    
    async def get_folder_hierarchy(self, root_folder_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get folder hierarchy starting from root or specific folder"""
        cursor = self.connection.cursor()
        
        try:
            # Use a single query and build the hierarchy in Python
            cursor.execute("""
                SELECT id, path, name, parent_id, level, file_count, last_indexed,
                       (SELECT COUNT(*) FROM folders sub WHERE sub.parent_id = f.id) as subfolder_count
                FROM folders f
                ORDER BY level, name
            """)
            
            rows = cursor.fetchall()
            
            folders = {row['id']: dict(row, children=[]) for row in rows}
            root_folders = []
            
            for folder_id, folder in folders.items():
                if folder['parent_id'] is None:
                    root_folders.append(folder)
                elif folder['parent_id'] in folders:
                    folders[folder['parent_id']]['children'].append(folder)

            # If a root_folder_id is specified, filter the results
            if root_folder_id:
                return [folders.get(root_folder_id)] if root_folder_id in folders else []

            return root_folders

        except Exception as e:
            logger.error(f"Error getting folder hierarchy: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def get_folder_by_id(self, folder_id: int) -> Optional[Dict[str, Any]]:
        """Get folder information by ID"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT id, path, name, parent_id, level, file_count, last_indexed
                FROM folders WHERE id = ?
            """, (folder_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'path': row['path'],
                    'name': row['name'],
                    'parent_id': row['parent_id'],
                    'level': row['level'],
                    'file_count': row['file_count'],
                    'last_indexed': row['last_indexed']
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting folder {folder_id}: {str(e)}")
            raise
    
    async def get_files_in_folder_recursive(self, folder_id: int) -> List[Dict[str, Any]]:
        """Get all files in a folder and its subfolders recursively"""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                WITH RECURSIVE folder_tree AS (
                    SELECT id FROM folders WHERE id = ?
                    UNION ALL
                    SELECT f.id FROM folders f
                    INNER JOIN folder_tree ft ON f.parent_id = ft.id
                )
                SELECT f.id, f.file_path, f.file_name, f.file_type, f.file_size, 
                       f.last_modified, f.folder_id
                FROM files f
                INNER JOIN folder_tree ft ON f.folder_id = ft.id
                ORDER BY f.file_name
            """, (folder_id,))
            
            return [
                {
                    'id': row['id'],
                    'file_path': row['file_path'],
                    'file_name': row['file_name'],
                    'file_type': row['file_type'],
                    'file_size': row['file_size'],
                    'last_modified': row['last_modified'],
                    'folder_id': row['folder_id']
                }
                for row in cursor.fetchall()
            ]
            
        except Exception as e:
            logger.error(f"Error getting files in folder {folder_id}: {str(e)}")
            raise
    
    async def get_file_content(self, file_id: int) -> Optional[str]:
        """Get file content from document chunks"""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                SELECT content FROM document_chunks 
                WHERE file_id = ? 
                ORDER BY chunk_index
            """, (file_id,))
            
            chunks = cursor.fetchall()
            if chunks:
                return '\n'.join([chunk['content'] for chunk in chunks])
            return None
            
        except Exception as e:
            logger.error(f"Error getting file content for {file_id}: {str(e)}")
            return None
    
    async def update_file_location(self, file_id: int, new_path: str) -> None:
        """Update file location after organization"""
        cursor = self.connection.cursor()
        
        try:
            new_name = Path(new_path).name
            cursor.execute("""
                UPDATE files 
                SET file_path = ?, file_name = ?
                WHERE id = ?
            """, (new_path, new_name, file_id))
            
            self.connection.commit()
            logger.debug(f"Updated file location: {file_id} -> {new_path}")
            
        except Exception as e:
            logger.error(f"Error updating file location: {str(e)}")
            raise
    
    async def update_file_location_by_path(self, old_path: str, new_path: str) -> None:
        """Update file location by path"""
        cursor = self.connection.cursor()
        
        try:
            new_name = Path(new_path).name
            cursor.execute("""
                UPDATE files 
                SET file_path = ?, file_name = ?
                WHERE file_path = ?
            """, (new_path, new_name, old_path))
            
            self.connection.commit()
            logger.debug(f"Updated file location: {old_path} -> {new_path}")
            
        except Exception as e:
            logger.error(f"Error updating file location by path: {str(e)}")
            raise
    
    async def save_organisation_actions(self, folder_id: int, actions: List[Dict]) -> None:
        """Save organization actions for rollback capability"""
        cursor = self.connection.cursor()
        
        try:
            for action in actions:
                cursor.execute("""
                    INSERT INTO organisation_actions 
                    (folder_id, action_type, source_path, target_path, classification, 
                     confidence, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    folder_id,
                    action['action_type'],
                    action['source_path'],
                    action['target_path'],
                    action.get('classification'),
                    action.get('confidence'),
                    action['status'],
                    action.get('error')
                ))
            
            self.connection.commit()
            logger.info(f"Saved {len(actions)} organization actions")
            
        except Exception as e:
            logger.error(f"Error saving organization actions: {str(e)}")
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
        """Get list of indexed folders with accurate, recursive file counts."""
        cursor = self.connection.cursor()
        try:
            # Get all folders first
            cursor.execute("SELECT id, path, name, last_indexed, parent_id FROM folders ORDER BY last_indexed DESC")
            all_folders = cursor.fetchall()

            if not all_folders:
                return []

            folder_map = {f['id']: dict(f, children=[]) for f in all_folders}
            
            # Build the hierarchy
            for folder_id, folder_data in folder_map.items():
                parent_id = folder_data['parent_id']
                if parent_id and parent_id in folder_map:
                    folder_map[parent_id]['children'].append(folder_data)

            # Get file counts for all folders at once
            cursor.execute("SELECT folder_id, COUNT(*) as count FROM files GROUP BY folder_id")
            file_counts = {row['folder_id']: row['count'] for row in cursor.fetchall()}

            def get_recursive_file_count(folder_id: int) -> int:
                """Recursively calculate file count for a folder and its children."""
                count = file_counts.get(folder_id, 0)
                for child in folder_map.get(folder_id, {}).get('children', []):
                    count += get_recursive_file_count(child['id'])
                return count

            # Calculate counts and prepare the final list of root folders
            root_folders = []
            for folder in all_folders:
                if folder['parent_id'] is None:
                    folder_id = folder['id']
                    total_files = get_recursive_file_count(folder_id)
                    
                    # Update the database for consistency
                    cursor.execute("UPDATE folders SET file_count = ? WHERE id = ?", (total_files, folder_id))

                    root_folders.append({
                        'id': folder_id,
                        'path': folder['path'],
                        'name': folder['name'],
                        'file_count': total_files,
                        'last_indexed': folder['last_indexed']
                    })
            
            self.connection.commit()
            logger.info(f"Retrieved and updated {len(root_folders)} root folders with recursive file counts.")
            return root_folders

        except Exception as e:
            logger.error(f"Error getting indexed folders: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def remove_folder(self, folder_id: int):
        """Remove a folder and all its associated data"""
        cursor = self.connection.cursor()
        try:
            # Get folder info before deletion
            cursor.execute("SELECT path FROM folders WHERE id = ?", (folder_id,))
            folder = cursor.fetchone()
            
            if folder:
                logger.info(f"Removing folder: {folder['path']}")
                cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
                self.connection.commit()
                logger.info("Folder removed successfully")
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
            cursor.execute("DELETE FROM organisation_actions")
            cursor.execute("DELETE FROM file_classifications")
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
