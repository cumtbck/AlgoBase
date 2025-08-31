"""
Utility functions for CLAUDE backend
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
import time

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

def ensure_directory_exists(path: str):
    """Ensure directory exists, create if not"""
    Path(path).mkdir(parents=True, exist_ok=True)

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash for {file_path}: {str(e)}")
        return ""

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {str(e)}")
        return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename or "unnamed"

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file safely"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {str(e)}")
        return None

def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """Save JSON file safely"""
    try:
        ensure_directory_exists(str(Path(file_path).parent))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {str(e)}")
        return False

def get_supported_languages() -> List[str]:
    """Get list of supported programming languages"""
    return [
        "python", "javascript", "typescript", "java", "cpp", "c", 
        "go", "rust", "php", "ruby", "swift", "kotlin", "csharp"
    ]

def get_language_extensions() -> Dict[str, List[str]]:
    """Get mapping of languages to file extensions"""
    return {
        "python": [".py", ".pyw"],
        "javascript": [".js", ".mjs", ".cjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "cpp": [".cpp", ".cxx", ".cc", ".c++", ".hpp", ".hxx"],
        "c": [".c", ".h"],
        "go": [".go"],
        "rust": [".rs"],
        "php": [".php"],
        "ruby": [".rb"],
        "swift": [".swift"],
        "kotlin": [".kt"],
        "csharp": [".cs", ".csx"]
    }

def detect_language_from_file(file_path: str) -> Optional[str]:
    """Detect programming language from file extension"""
    ext = Path(file_path).suffix.lower()
    lang_extensions = get_language_extensions()
    
    for lang, extensions in lang_extensions.items():
        if ext in extensions:
            return lang
    
    return None

def is_text_file(file_path: str) -> bool:
    """Check if file is a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # Try to read first 1KB
        return True
    except Exception:
        return False

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information"""
    try:
        path = Path(file_path)
        stat = path.stat()
        
        return {
            "path": str(path),
            "name": path.name,
            "extension": path.suffix,
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "last_modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "is_text": is_text_file(file_path) if path.is_file() else False,
            "language": detect_language_from_file(file_path) if path.is_file() else None,
            "hash": calculate_file_hash(file_path) if path.is_file() else None
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {str(e)}")
        return {"path": file_path, "error": str(e)}

def find_files_by_pattern(directory: str, pattern: str = "*", recursive: bool = True) -> List[str]:
    """Find files matching a pattern"""
    try:
        path = Path(directory)
        if recursive:
            return [str(f) for f in path.rglob(pattern) if f.is_file()]
        else:
            return [str(f) for f in path.glob(pattern) if f.is_file()]
    except Exception as e:
        logger.error(f"Error finding files in {directory}: {str(e)}")
        return []

def create_backup(original_path: str, backup_dir: str = "backups") -> Optional[str]:
    """Create a backup of a file"""
    try:
        original = Path(original_path)
        if not original.exists():
            return None
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{original.stem}_{timestamp}{original.suffix}"
        backup_file = backup_path / backup_filename
        
        # Copy file
        import shutil
        shutil.copy2(original, backup_file)
        
        logger.info(f"Created backup: {backup_file}")
        return str(backup_file)
        
    except Exception as e:
        logger.error(f"Error creating backup for {original_path}: {str(e)}")
        return None

def cleanup_old_backups(backup_dir: str = "backups", max_age_days: int = 30) -> int:
    """Clean up old backup files"""
    try:
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        cleaned_count = 0
        
        for backup_file in backup_path.glob("*"):
            if backup_file.is_file():
                file_age = current_time - backup_file.stat().st_mtime
                if file_age > max_age_seconds:
                    backup_file.unlink()
                    cleaned_count += 1
                    logger.info(f"Cleaned up old backup: {backup_file}")
        
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Error cleaning up backups: {str(e)}")
        return 0

def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate configuration and return list of errors"""
    errors = []
    
    # Required fields
    required_fields = ["llm_model", "vector_db_path", "storage_type"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate storage type
    if config.get("storage_type") not in ["local", "cloud"]:
        errors.append("storage_type must be 'local' or 'cloud'")
    
    # Validate API port
    api_port = config.get("api_port")
    if api_port and not (1 <= api_port <= 65535):
        errors.append("api_port must be between 1 and 65535")
    
    # Validate log level
    log_level = config.get("log_level", "INFO").upper()
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        errors.append("log_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    
    return errors

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries"""
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    import platform
    import psutil
    
    try:
        return {
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free
            }
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {"error": str(e)}