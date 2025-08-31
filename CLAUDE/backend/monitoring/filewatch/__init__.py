"""
File Watch Module

Provides file system monitoring and Git integration capabilities.
"""

from .file_watcher import FileWatcher, FileChangeEvent, GitIntegration, MonitoringManager

__all__ = ["FileWatcher", "FileChangeEvent", "GitIntegration", "MonitoringManager"]