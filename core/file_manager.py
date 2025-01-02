"""
Core file management functionality for the image processing system.
Handles file operations, temporary storage, and cleanup.
"""

from pathlib import Path
from typing import Union, Optional, List, BinaryIO
import tempfile
import shutil
import os
import logging
from PIL import Image
from io import BytesIO

class FileManager:
    """Manages file operations for the image processing system."""
    
    def __init__(self, temp_dir: Optional[Union[str, Path]] = None):
        """
        Initialize file manager.
        
        Args:
            temp_dir: Optional custom temporary directory path
        """
        self.logger = logging.getLogger('FileManager')
        
        if temp_dir:
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.temp_dir = Path(tempfile.mkdtemp(prefix='img_proc_'))
            
        self.temp_files: List[Path] = []

    def create_temp_directory(self, prefix: str = "") -> Path:
        """
        Create a new temporary directory.
        
        Args:
            prefix: Optional prefix for directory name
            
        Returns:
            Path to new temporary directory
        """
        temp_path = Path(tempfile.mkdtemp(prefix=prefix, dir=self.temp_dir))
        return temp_path

    def create_temp_file(self, 
                        suffix: str = "", 
                        prefix: str = "",
                        directory: Optional[Union[str, Path]] = None) -> Path:
        """
        Create a temporary file.
        
        Args:
            suffix: File extension
            prefix: Filename prefix
            directory: Optional specific directory
            
        Returns:
            Path to new temporary file
        """
        if directory:
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            dir_path = self.temp_dir
            
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix=prefix,
            dir=dir_path,
            delete=False
        )
        
        temp_path = Path(temp_file.name)
        self.temp_files.append(temp_path)
        return temp_path

    def save_image(self,
                  image: Union[Image.Image, bytes, BytesIO],
                  path: Union[str, Path],
                  format: Optional[str] = None) -> None:
        """
        Save image to file.
        
        Args:
            image: Image to save
            path: Output path
            format: Optional format override
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if isinstance(image, (bytes, BytesIO)):
                if isinstance(image, bytes):
                    image = BytesIO(image)
                image = Image.open(image)
                
            image.save(output_path, format=format)
            
        except Exception as e:
            self.logger.error(f"Error saving image: {e}")
            raise

    def load_image(self, path: Union[str, Path, bytes, BytesIO]) -> Image.Image:
        """
        Load image from file or binary data.
        
        Args:
            path: Image source
            
        Returns:
            PIL Image object
        """
        try:
            if isinstance(path, (str, Path)):
                path = Path(path)
                if not path.exists():
                    raise FileNotFoundError(f"Image not found: {path}")
                return Image.open(path)
            elif isinstance(path, bytes):
                return Image.open(BytesIO(path))
            elif isinstance(path, BytesIO):
                return Image.open(path)
            else:
                raise ValueError(f"Unsupported image source type: {type(path)}")
                
        except Exception as e:
            self.logger.error(f"Error loading image: {e}")
            raise

    def cleanup_temp_file(self, path: Union[str, Path]) -> None:
        """
        Delete a specific temporary file.
        
        Args:
            path: Path to file to delete
        """
        try:
            path = Path(path)
            if path.exists():
                path.unlink()
            if path in self.temp_files:
                self.temp_files.remove(path)
                
        except Exception as e:
            self.logger.error(f"Error cleaning up file {path}: {e}")

    def cleanup_temp_directory(self, path: Union[str, Path]) -> None:
        """
        Delete a temporary directory and its contents.
        
        Args:
            path: Path to directory to delete
        """
        try:
            path = Path(path)
            if path.exists():
                shutil.rmtree(path)
                
        except Exception as e:
            self.logger.error(f"Error cleaning up directory {path}: {e}")

    def cleanup_all(self) -> None:
        """Clean up all temporary files and directories."""
        # Clean up individual temp files
        for temp_file in self.temp_files[:]:
            self.cleanup_temp_file(temp_file)
            
        # Clean up temp directory
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.error(f"Error cleaning up temp directory: {e}")

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.cleanup_all()