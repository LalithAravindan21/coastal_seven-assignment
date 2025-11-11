import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class KnowledgeBase:
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Files table - stores metadata about uploaded files
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_path TEXT,
                file_size INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0
            )
        ''')
        
        # Chunks table - stores processed content chunks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                content_type TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        ''')
        
        # Queries table - stores user queries and responses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                response_text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_file(self, filename: str, file_type: str, file_path: str = None, file_size: int = 0) -> int:
        """Add a file record to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO files (filename, file_type, file_path, file_size)
            VALUES (?, ?, ?, ?)
        ''', (filename, file_type, file_path, file_size))
        
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id
    
    def mark_file_processed(self, file_id: int):
        """Mark a file as processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE files SET processed = 1 WHERE id = ?
        ''', (file_id,))
        
        conn.commit()
        conn.close()
    
    def add_chunk(self, file_id: int, chunk_index: int, content: str, content_type: str, metadata: Dict = None):
        """Add a content chunk to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
            INSERT INTO chunks (file_id, chunk_index, content, content_type, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (file_id, chunk_index, content, content_type, metadata_json))
        
        conn.commit()
        conn.close()
    
    def get_all_chunks(self, content_type: str = None) -> List[Dict]:
        """Retrieve all chunks, optionally filtered by content type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if content_type:
            cursor.execute('''
                SELECT c.id, c.file_id, c.chunk_index, c.content, c.content_type, c.metadata,
                       f.filename, f.file_type
                FROM chunks c
                JOIN files f ON c.file_id = f.id
                WHERE c.content_type = ?
                ORDER BY f.id, c.chunk_index
            ''', (content_type,))
        else:
            cursor.execute('''
                SELECT c.id, c.file_id, c.chunk_index, c.content, c.content_type, c.metadata,
                       f.filename, f.file_type
                FROM chunks c
                JOIN files f ON c.file_id = f.id
                ORDER BY f.id, c.chunk_index
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        chunks = []
        for row in rows:
            chunks.append({
                'id': row[0],
                'file_id': row[1],
                'chunk_index': row[2],
                'content': row[3],
                'content_type': row[4],
                'metadata': json.loads(row[5]) if row[5] else {},
                'filename': row[6],
                'file_type': row[7]
            })
        
        return chunks
    
    def get_file_chunks(self, file_id: int) -> List[Dict]:
        """Get all chunks for a specific file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, chunk_index, content, content_type, metadata
            FROM chunks
            WHERE file_id = ?
            ORDER BY chunk_index
        ''', (file_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        chunks = []
        for row in rows:
            chunks.append({
                'id': row[0],
                'chunk_index': row[1],
                'content': row[2],
                'content_type': row[3],
                'metadata': json.loads(row[4]) if row[4] else {}
            })
        
        return chunks
    
    def save_query(self, query_text: str, response_text: str = None):
        """Save a query and its response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO queries (query_text, response_text)
            VALUES (?, ?)
        ''', (query_text, response_text))
        
        conn.commit()
        conn.close()
    
    def get_all_files(self) -> List[Dict]:
        """Get all files in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, file_type, file_path, file_size, upload_date, processed
            FROM files
            ORDER BY upload_date DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        files = []
        for row in rows:
            files.append({
                'id': row[0],
                'filename': row[1],
                'file_type': row[2],
                'file_path': row[3],
                'file_size': row[4],
                'upload_date': row[5],
                'processed': bool(row[6])
            })
        
        return files
    
    def get_all_queries(self) -> List[Dict]:
        """Get all saved queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, query_text, response_text, timestamp
            FROM queries
            ORDER BY timestamp DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        queries = []
        for row in rows:
            queries.append({
                'id': row[0],
                'query_text': row[1],
                'response_text': row[2],
                'timestamp': row[3]
            })
        
        return queries
    
    def clear_all_data(self):
        """Clear all data from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete all chunks first (foreign key constraint)
        cursor.execute('DELETE FROM chunks')
        
        # Delete all files
        cursor.execute('DELETE FROM files')
        
        # Delete all queries
        cursor.execute('DELETE FROM queries')
        
        conn.commit()
        conn.close()
    
    def delete_query_history(self):
        """Delete all query history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM queries')
        
        conn.commit()
        conn.close()

