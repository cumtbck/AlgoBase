"""
Storage Manager

Provides unified storage interface for local and cloud storage.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class StorageItem:
    """Represents a storage item"""
    path: str
    size: int
    last_modified: float
    is_directory: bool
    metadata: Dict[str, Any]

class StorageInterface(ABC):
    """Abstract interface for storage operations"""
    
    @abstractmethod
    async def save(self, path: str, content: Union[str, bytes], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save content to storage"""
        pass
    
    @abstractmethod
    async def load(self, path: str) -> Optional[Union[str, bytes]]:
        """Load content from storage"""
        pass
    
    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete item from storage"""
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if item exists in storage"""
        pass
    
    @abstractmethod
    async def list(self, path: str = "", recursive: bool = False) -> List[StorageItem]:
        """List items in storage"""
        pass
    
    @abstractmethod
    async def get_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for item"""
        pass
    
    @abstractmethod
    async def set_metadata(self, path: str, metadata: Dict[str, Any]) -> bool:
        """Set metadata for item"""
        pass

class LocalStorage(StorageInterface):
    """Local file system storage implementation"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.local_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage initialized at {self.base_path}")
    
    def _get_full_path(self, path: str) -> Path:
        """Get full path from relative path"""
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return full_path
    
    async def save(self, path: str, content: Union[str, bytes], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save content to local storage"""
        try:
            full_path = self._get_full_path(path)
            
            if isinstance(content, str):
                full_path.write_text(content, encoding='utf-8')
            else:
                full_path.write_bytes(content)
            
            # Save metadata if provided
            if metadata:
                metadata_path = full_path.with_suffix(full_path.suffix + '.meta')
                metadata_path.write_text(json.dumps(metadata), encoding='utf-8')
            
            logger.debug(f"Saved content to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to local storage: {str(e)}")
            return False
    
    async def load(self, path: str) -> Optional[Union[str, bytes]]:
        """Load content from local storage"""
        try:
            full_path = self._get_full_path(path)
            
            if not full_path.exists():
                return None
            
            # Try to detect if it's text or binary
            try:
                return full_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                return full_path.read_bytes()
                
        except Exception as e:
            logger.error(f"Error loading from local storage: {str(e)}")
            return None
    
    async def delete(self, path: str) -> bool:
        """Delete item from local storage"""
        try:
            full_path = self._get_full_path(path)
            
            if full_path.exists():
                full_path.unlink()
                
                # Delete metadata file if it exists
                metadata_path = full_path.with_suffix(full_path.suffix + '.meta')
                if metadata_path.exists():
                    metadata_path.unlink()
                
                logger.debug(f"Deleted {path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting from local storage: {str(e)}")
            return False
    
    async def exists(self, path: str) -> bool:
        """Check if item exists in local storage"""
        try:
            full_path = self._get_full_path(path)
            return full_path.exists()
        except Exception as e:
            logger.error(f"Error checking existence in local storage: {str(e)}")
            return False
    
    async def list(self, path: str = "", recursive: bool = False) -> List[StorageItem]:
        """List items in local storage"""
        try:
            base_path = self._get_full_path(path)
            
            if not base_path.exists():
                return []
            
            items = []
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for item_path in base_path.glob(pattern):
                if item_path.name.endswith('.meta'):
                    continue
                
                relative_path = item_path.relative_to(self.base_path)
                
                # Load metadata if exists
                metadata = {}
                metadata_path = item_path.with_suffix(item_path.suffix + '.meta')
                if metadata_path.exists():
                    try:
                        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
                    except Exception:
                        pass
                
                stat = item_path.stat()
                
                items.append(StorageItem(
                    path=str(relative_path),
                    size=stat.st_size,
                    last_modified=stat.st_mtime,
                    is_directory=item_path.is_dir(),
                    metadata=metadata
                ))
            
            return sorted(items, key=lambda x: (not x.is_directory, x.path))
            
        except Exception as e:
            logger.error(f"Error listing local storage: {str(e)}")
            return []
    
    async def get_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for item"""
        try:
            full_path = self._get_full_path(path)
            metadata_path = full_path.with_suffix(full_path.suffix + '.meta')
            
            if metadata_path.exists():
                return json.loads(metadata_path.read_text(encoding='utf-8'))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting metadata from local storage: {str(e)}")
            return None
    
    async def set_metadata(self, path: str, metadata: Dict[str, Any]) -> bool:
        """Set metadata for item"""
        try:
            full_path = self._get_full_path(path)
            metadata_path = full_path.with_suffix(full_path.suffix + '.meta')
            
            metadata_path.write_text(json.dumps(metadata), encoding='utf-8')
            return True
            
        except Exception as e:
            logger.error(f"Error setting metadata in local storage: {str(e)}")
            return False

class CloudStorage(StorageInterface):
    """Cloud storage implementation (placeholder for future implementation)"""
    
    def __init__(self, bucket_name: str, access_key: str, secret_key: str):
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key
        logger.info(f"Cloud storage initialized for bucket: {bucket_name}")
    
    async def save(self, path: str, content: Union[str, bytes], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save content to cloud storage"""
        logger.warning("Cloud storage not fully implemented")
        return False
    
    async def load(self, path: str) -> Optional[Union[str, bytes]]:
        """Load content from cloud storage"""
        logger.warning("Cloud storage not fully implemented")
        return None
    
    async def delete(self, path: str) -> bool:
        """Delete item from cloud storage"""
        logger.warning("Cloud storage not fully implemented")
        return False
    
    async def exists(self, path: str) -> bool:
        """Check if item exists in cloud storage"""
        logger.warning("Cloud storage not fully implemented")
        return False
    
    async def list(self, path: str = "", recursive: bool = False) -> List[StorageItem]:
        """List items in cloud storage"""
        logger.warning("Cloud storage not fully implemented")
        return []
    
    async def get_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for item"""
        logger.warning("Cloud storage not fully implemented")
        return None
    
    async def set_metadata(self, path: str, metadata: Dict[str, Any]) -> bool:
        """Set metadata for item"""
        logger.warning("Cloud storage not fully implemented")
        return False

class StorageManager:
    """Unified storage manager"""
    
    def __init__(self, storage_type: Optional[str] = None):
        self.storage_type = storage_type or settings.storage_type
        self.storage: Optional[StorageInterface] = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage based on configuration"""
        if self.storage_type == "local":
            self.storage = LocalStorage()
        elif self.storage_type == "cloud":
            # Cloud storage would require additional configuration
            logger.warning("Cloud storage not configured, falling back to local storage")
            self.storage = LocalStorage()
        else:
            logger.warning(f"Unknown storage type: {self.storage_type}, using local storage")
            self.storage = LocalStorage()
    
    async def save(self, path: str, content: Union[str, bytes], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save content using configured storage"""
        if not self.storage:
            raise Exception("Storage not initialized")
        return await self.storage.save(path, content, metadata)
    
    async def load(self, path: str) -> Optional[Union[str, bytes]]:
        """Load content using configured storage"""
        if not self.storage:
            raise Exception("Storage not initialized")
        return await self.storage.load(path)
    
    async def delete(self, path: str) -> bool:
        """Delete item using configured storage"""
        if not self.storage:
            raise Exception("Storage not initialized")
        return await self.storage.delete(path)
    
    async def exists(self, path: str) -> bool:
        """Check if item exists using configured storage"""
        if not self.storage:
            raise Exception("Storage not initialized")
        return await self.storage.exists(path)
    
    async def list(self, path: str = "", recursive: bool = False) -> List[StorageItem]:
        """List items using configured storage"""
        if not self.storage:
            raise Exception("Storage not initialized")
        return await self.storage.list(path, recursive)
    
    async def get_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get metadata using configured storage"""
        if not self.storage:
            raise Exception("Storage not initialized")
        return await self.storage.get_metadata(path)
    
    async def set_metadata(self, path: str, metadata: Dict[str, Any]) -> bool:
        """Set metadata using configured storage"""
        if not self.storage:
            raise Exception("Storage not initialized")
        return await self.storage.set_metadata(path, metadata)
    
    async def backup_data(self, backup_path: str) -> Dict[str, Any]:
        """Create backup of storage data"""
        try:
            # Get all items
            all_items = await self.list(recursive=True)
            
            backup_data = {
                "storage_type": self.storage_type,
                "timestamp": asyncio.get_event_loop().time(),
                "items": []
            }
            
            # Backup each item
            for item in all_items:
                if not item.is_directory:
                    content = await self.load(item.path)
                    if content is not None:
                        backup_data["items"].append({
                            "path": item.path,
                            "content": content if isinstance(content, str) else content.hex(),
                            "is_binary": isinstance(content, bytes),
                            "metadata": item.metadata
                        })
            
            # Save backup
            backup_manager = StorageManager("local")
            await backup_manager.save(backup_path, json.dumps(backup_data, indent=2))
            
            logger.info(f"Created backup with {len(backup_data['items'])} items")
            
            return {
                "backup_path": backup_path,
                "items_backed_up": len(backup_data["items"]),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return {"error": str(e)}
    
    async def restore_data(self, backup_path: str) -> Dict[str, Any]:
        """Restore data from backup"""
        try:
            # Load backup
            backup_manager = StorageManager("local")
            backup_content = await backup_manager.load(backup_path)
            
            if not backup_content:
                return {"error": "Backup file not found or empty"}
            
            backup_data = json.loads(backup_content)
            
            # Restore items
            restored_count = 0
            for item_data in backup_data["items"]:
                content = item_data["content"]
                if item_data["is_binary"]:
                    content = bytes.fromhex(content)
                
                success = await self.save(
                    item_data["path"],
                    content,
                    item_data["metadata"]
                )
                
                if success:
                    restored_count += 1
            
            logger.info(f"Restored {restored_count} items from backup")
            
            return {
                "backup_path": backup_path,
                "items_restored": restored_count,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {str(e)}")
            return {"error": str(e)}
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            all_items = await self.list(recursive=True)
            
            total_files = sum(1 for item in all_items if not item.is_directory)
            total_directories = sum(1 for item in all_items if item.is_directory)
            total_size = sum(item.size for item in all_items if not item.is_directory)
            
            # File type analysis
            file_types = {}
            for item in all_items:
                if not item.is_directory:
                    ext = Path(item.path).suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                "storage_type": self.storage_type,
                "total_files": total_files,
                "total_directories": total_directories,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {"error": str(e)}