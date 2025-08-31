"""
File Watcher Module

Monitors file system changes and triggers appropriate actions
like re-indexing modified files.
"""

import logging
import asyncio
import time
from typing import Dict, List, Callable, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from threading import Thread
import queue

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from ..config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class FileChangeEvent:
    """Represents a file system change event"""
    event_type: str  # "created", "modified", "deleted", "moved"
    file_path: str
    timestamp: float
    is_directory: bool = False

class CodebaseEventHandler(FileSystemEventHandler):
    """Handles file system events for codebase monitoring"""
    
    def __init__(self, callback: Callable[[FileChangeEvent], None]):
        self.callback = callback
        self.event_queue = queue.Queue()
        self.debounce_time = 1.0  # Debounce events within 1 second
        self.pending_events: Dict[str, float] = {}
        self.debounce_task: Optional[asyncio.Task] = None
    
    def on_created(self, event):
        """Handle file creation"""
        if not event.is_directory:
            self._enqueue_event("created", event.src_path)
    
    def on_modified(self, event):
        """Handle file modification"""
        if not event.is_directory:
            self._enqueue_event("modified", event.src_path)
    
    def on_deleted(self, event):
        """Handle file deletion"""
        if not event.is_directory:
            self._enqueue_event("deleted", event.src_path)
    
    def on_moved(self, event):
        """Handle file movement"""
        if not event.is_directory:
            self._enqueue_event("moved", event.dest_path)
    
    def _enqueue_event(self, event_type: str, file_path: str):
        """Enqueue event with debouncing"""
        current_time = time.time()
        
        # Add to pending events
        self.pending_events[file_path] = current_time
        
        # Schedule debounce processing
        if self.debounce_task is None or self.debounce_task.done():
            loop = asyncio.get_event_loop()
            self.debounce_task = loop.create_task(self._process_pending_events())
    
    async def _process_pending_events(self):
        """Process pending events with debouncing"""
        await asyncio.sleep(self.debounce_time)
        
        current_time = time.time()
        expired_events = [
            path for path, timestamp in self.pending_events.items()
            if current_time - timestamp >= self.debounce_time
        ]
        
        for file_path in expired_events:
            # Create event (use "modified" as default for debounced events)
            event = FileChangeEvent(
                event_type="modified",
                file_path=file_path,
                timestamp=current_time
            )
            
            # Call callback
            try:
                self.callback(event)
            except Exception as e:
                logger.error(f"Error in file change callback: {str(e)}")
            
            # Remove from pending
            del self.pending_events[file_path]

class FileWatcher:
    """Monitors file system changes in codebase directories"""
    
    def __init__(self, watch_directories: Optional[List[str]] = None):
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog library is required for file monitoring")
        
        self.watch_directories = watch_directories or settings.watch_directories
        self.observer = Observer()
        self.event_handlers: List[CodebaseEventHandler] = []
        self.change_callbacks: List[Callable[[FileChangeEvent], None]] = []
        self.is_running = False
        self.watched_paths: Set[str] = set()
        
        # Supported file extensions
        self.supported_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go',
            '.rs', '.php', '.rb', '.swift', '.kt', '.cs', '.h', '.hpp'
        }
    
    def add_change_callback(self, callback: Callable[[FileChangeEvent], None]):
        """Add callback for file change events"""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[FileChangeEvent], None]):
        """Remove callback for file change events"""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)
    
    def _should_watch_file(self, file_path: str) -> bool:
        """Check if file should be watched based on extension"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def _handle_file_change(self, event: FileChangeEvent):
        """Handle file change event"""
        # Only process supported file types
        if not self._should_watch_file(event.file_path):
            return
        
        logger.debug(f"File {event.event_type}: {event.file_path}")
        
        # Call all registered callbacks
        for callback in self.change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in file change callback: {str(e)}")
    
    def start_watching(self):
        """Start watching configured directories"""
        if self.is_running:
            logger.warning("File watcher is already running")
            return
        
        try:
            # Create event handler
            event_handler = CodebaseEventHandler(self._handle_file_change)
            self.event_handlers.append(event_handler)
            
            # Add watches for each directory
            for directory in self.watch_directories:
                directory_path = Path(directory)
                if directory_path.exists():
                    self.observer.schedule(
                        event_handler,
                        str(directory_path),
                        recursive=True
                    )
                    self.watched_paths.add(str(directory_path))
                    logger.info(f"Watching directory: {directory}")
                else:
                    logger.warning(f"Directory not found: {directory}")
            
            # Start observer
            self.observer.start()
            self.is_running = True
            
            logger.info(f"File watcher started, monitoring {len(self.watched_paths)} directories")
            
        except Exception as e:
            logger.error(f"Error starting file watcher: {str(e)}")
            raise
    
    def stop_watching(self):
        """Stop watching directories"""
        if not self.is_running:
            return
        
        try:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            self.watched_paths.clear()
            self.event_handlers.clear()
            
            logger.info("File watcher stopped")
            
        except Exception as e:
            logger.error(f"Error stopping file watcher: {str(e)}")
    
    def add_watch_directory(self, directory: str):
        """Add a new directory to watch"""
        if self.is_running:
            logger.warning("Cannot add directory while watcher is running")
            return
        
        if directory not in self.watch_directories:
            self.watch_directories.append(directory)
            logger.info(f"Added watch directory: {directory}")
    
    def remove_watch_directory(self, directory: str):
        """Remove a directory from watch list"""
        if directory in self.watch_directories:
            self.watch_directories.remove(directory)
            logger.info(f"Removed watch directory: {directory}")
    
    def get_watched_directories(self) -> List[str]:
        """Get list of currently watched directories"""
        return list(self.watched_paths)
    
    def get_watcher_stats(self) -> Dict[str, Any]:
        """Get file watcher statistics"""
        return {
            "is_running": self.is_running,
            "watched_directories": list(self.watched_paths),
            "configured_directories": self.watch_directories,
            "supported_extensions": list(self.supported_extensions),
            "registered_callbacks": len(self.change_callbacks)
        }

class GitIntegration:
    """Git integration for version control hooks"""
    
    def __init__(self, codebase_root: str):
        self.codebase_root = Path(codebase_root)
        self.git_dir = self.codebase_root / '.git'
    
    def is_git_repository(self) -> bool:
        """Check if current directory is a git repository"""
        return self.git_dir.exists()
    
    def get_staged_files(self) -> List[str]:
        """Get list of staged files"""
        if not self.is_git_repository():
            return []
        
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=self.codebase_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting staged files: {str(e)}")
            return []
    
    def get_modified_files(self) -> List[str]:
        """Get list of modified files"""
        if not self.is_git_repository():
            return []
        
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                cwd=self.codebase_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting modified files: {str(e)}")
            return []
    
    def setup_git_hooks(self) -> bool:
        """Set up git hooks for automatic indexing"""
        if not self.is_git_repository():
            logger.warning("Not a git repository, cannot set up hooks")
            return False
        
        try:
            hooks_dir = self.git_dir / 'hooks'
            hooks_dir.mkdir(exist_ok=True)
            
            # Post-commit hook
            post_commit_hook = hooks_dir / 'post-commit'
            hook_content = '''#!/bin/bash
# CLAUDE post-commit hook
echo "Running CLAUDE indexing..."
curl -X POST http://localhost:8000/api/index/commit \
  -H "Content-Type: application/json" \
  -d '{"action": "post-commit", "repository": "'$(pwd)'"}'
'''
            
            with open(post_commit_hook, 'w') as f:
                f.write(hook_content)
            
            # Make hook executable
            post_commit_hook.chmod(0o755)
            
            logger.info("Git hooks set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up git hooks: {str(e)}")
            return False

class MonitoringManager:
    """Manages all monitoring components"""
    
    def __init__(self, codebase_root: str):
        self.codebase_root = codebase_root
        self.file_watcher = FileWatcher()
        self.git_integration = GitIntegration(codebase_root)
        self.change_callbacks: List[Callable[[FileChangeEvent], None]] = []
        
        # Set up default callback
        self.file_watcher.add_change_callback(self._handle_file_change)
    
    def add_change_callback(self, callback: Callable[[FileChangeEvent], None]):
        """Add callback for file change events"""
        self.change_callbacks.append(callback)
    
    def _handle_file_change(self, event: FileChangeEvent):
        """Handle file change event"""
        # Forward to all registered callbacks
        for callback in self.change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in monitoring callback: {str(e)}")
    
    def start_monitoring(self):
        """Start all monitoring components"""
        try:
            # Start file watcher
            self.file_watcher.start_watching()
            
            # Set up git hooks if available
            if self.git_integration.is_git_repository():
                self.git_integration.setup_git_hooks()
            
            logger.info("Monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {str(e)}")
            raise
    
    def stop_monitoring(self):
        """Stop all monitoring components"""
        try:
            self.file_watcher.stop_watching()
            logger.info("Monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping monitoring: {str(e)}")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics"""
        return {
            "file_watcher": self.file_watcher.get_watcher_stats(),
            "git_integration": {
                "is_git_repository": self.git_integration.is_git_repository(),
                "git_dir_exists": self.git_integration.git_dir.exists()
            },
            "codebase_root": str(self.codebase_root)
        }
    
    def add_watch_directory(self, directory: str):
        """Add directory to watch list"""
        self.file_watcher.add_watch_directory(directory)
    
    def get_staged_files(self) -> List[str]:
        """Get staged files from git"""
        return self.git_integration.get_staged_files()
    
    def get_modified_files(self) -> List[str]:
        """Get modified files from git"""
        return self.git_integration.get_modified_files()