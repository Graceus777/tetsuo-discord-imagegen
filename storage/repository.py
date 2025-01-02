from PIL import Image
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from io import BytesIO
import os

from core.image_processor import BaseImageProcessor
from core.effect_processor import EffectProcessor
from core.utils import ImageUtils

class ImageRepository:
    """
    Manages storage and retrieval of processed images with metadata.
    """
    
    def __init__(self, db_path: Union[str, Path], storage_path: Union[str, Path]):
        """
        Initialize image repository.
        
        Args:
            db_path: Path to SQLite database file
            storage_path: Path to image storage directory
        """
        self.logger = logging.getLogger('ImageRepository')
        self.db_path = Path(db_path)
        self.storage_path = Path(storage_path)
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create images table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        creator_id TEXT NOT NULL,
                        creator_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_path TEXT NOT NULL,
                        tags TEXT,
                        parameters TEXT
                    )
                """)
                
                # Create tags table for efficient tag lookup
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_id INTEGER,
                        tag TEXT NOT NULL,
                        FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
                    )
                """)
                
                conn.commit()
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise

    def store_image(self,
                   image: Union[Image.Image, bytes, BytesIO],
                   title: str,
                   creator_id: str,
                   creator_name: str,
                   tags: Optional[List[str]] = None,
                   parameters: Optional[Dict[str, Any]] = None) -> int:
        """
        Store image with metadata.
        
        Args:
            image: Image to store
            title: Image title
            creator_id: Creator's unique identifier
            creator_name: Creator's display name
            tags: Optional list of tags
            parameters: Optional effect parameters used
            
        Returns:
            ID of stored image record
        """
        try:
            # Convert image to bytes if necessary
            if isinstance(image, Image.Image):
                img_bytes = BytesIO()
                image.save(img_bytes, format='PNG')
                img_bytes = img_bytes.getvalue()
            elif isinstance(image, BytesIO):
                img_bytes = image.getvalue()
            else:
                img_bytes = image
            
            # Generate unique filename
            filename = f"{title}_{creator_id}_{int(time.time())}.png"
            file_path = self.storage_path / filename
            
            # Save image file
            with open(file_path, 'wb') as f:
                f.write(img_bytes)
            
            # Store metadata in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert image record
                cursor.execute("""
                    INSERT INTO images (title, creator_id, creator_name, file_path, tags, parameters)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    title,
                    creator_id,
                    creator_name,
                    str(file_path),
                    json.dumps(tags or []),
                    json.dumps(parameters or {})
                ))
                
                image_id = cursor.lastrowid
                
                # Store tags
                if tags:
                    cursor.executemany("""
                        INSERT INTO tags (image_id, tag)
                        VALUES (?, ?)
                    """, [(image_id, tag) for tag in tags])
                
                conn.commit()
                
            return image_id
            
        except Exception as e:
            self.logger.error(f"Error storing image: {e}")
            raise

    def get_image(self, image_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve image and metadata by ID.
        
        Args:
            image_id: Image record ID
            
        Returns:
            Dictionary containing image data and metadata
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, creator_id, creator_name, created_at, file_path, tags, parameters
                    FROM images WHERE id = ?
                """, (image_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                # Load image file
                file_path = Path(row[5])
                if not file_path.exists():
                    self.logger.error(f"Image file not found: {file_path}")
                    return None
                    
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                return {
                    'id': row[0],
                    'title': row[1],
                    'creator_id': row[2],
                    'creator_name': row[3],
                    'created_at': row[4],
                    'image': image_data,
                    'tags': json.loads(row[6]),
                    'parameters': json.loads(row[7])
                }
                
        except Exception as e:
            self.logger.error(f"Error retrieving image: {e}")
            return None

    def search_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """
        Search for images by tags.
        
        Args:
            tags: List of tags to search for
            
        Returns:
            List of matching image records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query to match any of the provided tags
                placeholders = ','.join('?' * len(tags))
                cursor.execute(f"""
                    SELECT DISTINCT i.*
                    FROM images i
                    JOIN tags t ON i.id = t.image_id
                    WHERE t.tag IN ({placeholders})
                    ORDER BY i.created_at DESC
                """, tags)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'title': row[1],
                        'creator_id': row[2],
                        'creator_name': row[3],
                        'created_at': row[4],
                        'tags': json.loads(row[6]),
                        'parameters': json.loads(row[7])
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Error searching by tags: {e}")
            return []

    def delete_image(self, image_id: int) -> bool:
        """
        Delete image and associated metadata.
        
        Args:
            image_id: ID of image to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get file path before deleting record
                cursor.execute("SELECT file_path FROM images WHERE id = ?", (image_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                    
                file_path = Path(row[0])
                
                # Delete database record (tags will be cascade deleted)
                cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
                conn.commit()
                
                # Delete image file
                if file_path.exists():
                    file_path.unlink()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting image: {e}")
            return False

    def cleanup_orphaned_files(self) -> int:
        """
        Remove image files without corresponding database records.
        
        Returns:
            Number of files cleaned up
        """
        try:
            # Get all file paths from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path FROM images")
                db_files = {Path(row[0]) for row in cursor.fetchall()}
            
            # Check actual files in storage directory
            cleaned = 0
            for file_path in self.storage_path.glob('*'):
                if file_path.is_file() and file_path not in db_files:
                    file_path.unlink()
                    cleaned += 1
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning up files: {e}")
            return 0