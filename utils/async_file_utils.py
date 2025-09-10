"""
Async file operations utilities with proper error handling
"""
import aiofiles
import asyncio
import os
import json
from typing import Optional, Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class AsyncFileError(Exception):
    """Custom exception for async file operations"""
    pass


class AsyncFileUtils:
    """Utility class for async file operations with proper error handling"""
    
    @staticmethod
    async def read_json_file(file_path: str, encoding: str = 'utf-8') -> Optional[Dict[str, Any]]:
        """
        Read JSON file asynchronously with error handling
        
        Args:
            file_path: Path to the JSON file
            encoding: File encoding (default: utf-8)
            
        Returns:
            Parsed JSON data or None if error
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return None
            
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content = await f.read()
                return json.loads(content)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in file {file_path}: {e}")
            raise AsyncFileError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise AsyncFileError(f"Failed to read file {file_path}: {e}")
    
    @staticmethod
    async def write_json_file(file_path: str, data: Dict[str, Any], 
                            encoding: str = 'utf-8', ensure_ascii: bool = False, 
                            indent: int = 2) -> bool:
        """
        Write JSON file asynchronously with error handling
        
        Args:
            file_path: Path to the JSON file
            data: Data to write
            encoding: File encoding (default: utf-8)
            ensure_ascii: Ensure ASCII encoding (default: False)
            indent: JSON indentation (default: 2)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
                json_str = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
                await f.write(json_str)
            
            logger.debug(f"Successfully wrote JSON file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing JSON file {file_path}: {e}")
            raise AsyncFileError(f"Failed to write file {file_path}: {e}")
    
    @staticmethod
    async def read_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        Read text file asynchronously with error handling
        
        Args:
            file_path: Path to the text file
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content or None if error
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return None
            
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            raise AsyncFileError(f"Failed to read file {file_path}: {e}")
    
    @staticmethod
    async def write_text_file(file_path: str, content: str, 
                            encoding: str = 'utf-8') -> bool:
        """
        Write text file asynchronously with error handling
        
        Args:
            file_path: Path to the text file
            content: Content to write
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
                await f.write(content)
            
            logger.debug(f"Successfully wrote text file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing text file {file_path}: {e}")
            raise AsyncFileError(f"Failed to write file {file_path}: {e}")
    
    @staticmethod
    async def read_binary_file(file_path: str) -> Optional[bytes]:
        """
        Read binary file asynchronously with error handling
        
        Args:
            file_path: Path to the binary file
            
        Returns:
            File content as bytes or None if error
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return None
            
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading binary file {file_path}: {e}")
            raise AsyncFileError(f"Failed to read file {file_path}: {e}")
    
    @staticmethod
    async def write_binary_file(file_path: str, content: bytes) -> bool:
        """
        Write binary file asynchronously with error handling
        
        Args:
            file_path: Path to the binary file
            content: Content to write as bytes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            logger.debug(f"Successfully wrote binary file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing binary file {file_path}: {e}")
            raise AsyncFileError(f"Failed to write file {file_path}: {e}")
    
    @staticmethod
    async def file_exists(file_path: str) -> bool:
        """
        Check if file exists asynchronously
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            return os.path.exists(file_path)
        except Exception as e:
            logger.error(f"Error checking file existence {file_path}: {e}")
            return False
    
    @staticmethod
    async def delete_file(file_path: str) -> bool:
        """
        Delete file asynchronously with error handling
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Successfully deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File does not exist for deletion: {file_path}")
                return True  # Consider it successful if file doesn't exist
                
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise AsyncFileError(f"Failed to delete file {file_path}: {e}")
    
    @staticmethod
    async def ensure_directory(directory_path: str) -> bool:
        """
        Ensure directory exists asynchronously
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            logger.debug(f"Directory ensured: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            raise AsyncFileError(f"Failed to create directory {directory_path}: {e}")
    
    @staticmethod
    async def list_files(directory_path: str, pattern: str = "*") -> List[str]:
        """
        List files in directory asynchronously
        
        Args:
            directory_path: Path to the directory
            pattern: File pattern to match (default: "*")
            
        Returns:
            List of file paths
        """
        try:
            if not os.path.exists(directory_path):
                logger.warning(f"Directory does not exist: {directory_path}")
                return []
            
            files = []
            for filename in os.listdir(directory_path):
                if pattern == "*" or filename.endswith(pattern.replace("*", "")):
                    files.append(os.path.join(directory_path, filename))
            
            logger.debug(f"Found {len(files)} files in {directory_path}")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {directory_path}: {e}")
            raise AsyncFileError(f"Failed to list files in {directory_path}: {e}")
    
    @staticmethod
    async def cleanup_old_files(directory_path: str, max_age_seconds: int, 
                               pattern: str = "*") -> int:
        """
        Clean up old files asynchronously
        
        Args:
            directory_path: Path to the directory
            max_age_seconds: Maximum age of files in seconds
            pattern: File pattern to match (default: "*")
            
        Returns:
            Number of files deleted
        """
        try:
            import time
            current_time = time.time()
            deleted_count = 0
            
            files = await AsyncFileUtils.list_files(directory_path, pattern)
            
            for file_path in files:
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        await AsyncFileUtils.delete_file(file_path)
                        deleted_count += 1
                        logger.debug(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue
            
            logger.info(f"Cleaned up {deleted_count} old files from {directory_path}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up files in {directory_path}: {e}")
            raise AsyncFileError(f"Failed to cleanup files in {directory_path}: {e}")
