"""
Example Python utility functions for testing CLAUDE
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class FileUtils:
    """Utility class for file operations"""
    
    @staticmethod
    def read_file(file_path: str) -> Optional[str]:
        """Read file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    @staticmethod
    def write_file(file_path: str, content: str) -> bool:
        """Write content to file safely"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0


class DataProcessor:
    """Data processing utilities"""
    
    def __init__(self):
        self.data_cache = {}
    
    def process_json_data(self, json_data: str) -> Dict[str, Any]:
        """Process JSON data"""
        try:
            data = json.loads(json_data)
            return self._normalize_data(data)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return {}
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data structure"""
        normalized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                normalized[key.lower()] = value.strip()
            elif isinstance(value, (int, float)):
                normalized[key.lower()] = value
            elif isinstance(value, list):
                normalized[key.lower()] = len(value)
            else:
                normalized[key.lower()] = str(value)
        
        return normalized
    
    def cache_result(self, key: str, result: Any) -> None:
        """Cache processing result"""
        self.data_cache[key] = {
            'result': result,
            'timestamp': os.path.getmtime(__file__)
        }
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached result"""
        cached = self.data_cache.get(key)
        if cached:
            return cached['result']
        return None


class StringUtils:
    """String manipulation utilities"""
    
    @staticmethod
    def to_snake_case(text: str) -> str:
        """Convert text to snake_case"""
        import re
        # Replace spaces and punctuation with underscores
        text = re.sub(r'[\s\-\.]+', '_', text)
        # Remove special characters except underscores
        text = re.sub(r'[^a-zA-Z0-9_]', '', text)
        # Convert to lowercase
        return text.lower()
    
    @staticmethod
    def to_camel_case(text: str) -> str:
        """Convert text to camelCase"""
        words = text.replace('_', ' ').replace('-', ' ').split()
        if not words:
            return ""
        
        # First word lowercase, rest capitalized
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."


def main():
    """Main function for testing"""
    print("CLAUDE Test Codebase")
    print("=" * 30)
    
    # Test file operations
    file_utils = FileUtils()
    test_content = "This is a test file for CLAUDE indexing."
    file_utils.write_file("test_output.txt", test_content)
    
    # Test data processing
    processor = DataProcessor()
    test_json = '{"name": "Test Data", "value": 42, "items": ["a", "b", "c"]}'
    processed = processor.process_json_data(test_json)
    print(f"Processed data: {processed}")
    
    # Test string utilities
    test_string = "Hello World Test String"
    print(f"Snake case: {StringUtils.to_snake_case(test_string)}")
    print(f"Camel case: {StringUtils.to_camel_case(test_string)}")
    print(f"Truncated: {StringUtils.truncate_text(test_string, 15)}")


if __name__ == "__main__":
    main()