"""
Utility Module

Provides helper functions and utilities for the CLAUDE backend.
"""

from .helpers import (
    setup_logging,
    ensure_directory_exists,
    calculate_file_hash,
    get_file_size,
    format_file_size,
    sanitize_filename,
    load_json_file,
    save_json_file,
    get_supported_languages,
    get_language_extensions,
    detect_language_from_file,
    is_text_file,
    get_file_info,
    find_files_by_pattern,
    create_backup,
    cleanup_old_backups,
    validate_config,
    merge_configs,
    get_system_info
)

__all__ = [
    "setup_logging",
    "ensure_directory_exists",
    "calculate_file_hash",
    "get_file_size",
    "format_file_size",
    "sanitize_filename",
    "load_json_file",
    "save_json_file",
    "get_supported_languages",
    "get_language_extensions",
    "detect_language_from_file",
    "is_text_file",
    "get_file_info",
    "find_files_by_pattern",
    "create_backup",
    "cleanup_old_backups",
    "validate_config",
    "merge_configs",
    "get_system_info"
]