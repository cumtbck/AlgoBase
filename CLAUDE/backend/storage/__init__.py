"""
Storage Module

Provides unified storage interface for local and cloud storage operations.
"""

from .storage_manager import StorageManager, StorageItem, StorageInterface, LocalStorage, CloudStorage

__all__ = ["StorageManager", "StorageItem", "StorageInterface", "LocalStorage", "CloudStorage"]