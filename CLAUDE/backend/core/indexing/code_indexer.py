"""
Code Indexer Module

Handles code parsing, chunking, and vector storage for RAG functionality.
This module processes code files and creates searchable embeddings.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import asyncio
import ast
import json
from concurrent.futures import ThreadPoolExecutor

from ..config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""
    content: str
    file_path: str
    line_start: int
    line_end: int
    language: str
    chunk_type: str  # "function", "class", "import", "variable", "comment"
    name: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class FileIndex:
    """Index information for a file"""
    file_path: str
    language: str
    last_modified: float
    chunks: List[CodeChunk]
    total_chunks: int
    file_size: int

class CodeParser:
    """Parses code files and extracts structured information"""
    
    SUPPORTED_LANGUAGES = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.rb': 'ruby',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.cs': 'csharp',
        '.tsx': 'typescript',
        '.jsx': 'javascript'
    }
    
    @classmethod
    def get_language(cls, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        return cls.SUPPORTED_LANGUAGES.get(ext)
    
    @classmethod
    def parse_file(cls, file_path: str) -> List[CodeChunk]:
        """Parse a file and extract code chunks"""
        language = cls.get_language(file_path)
        if not language:
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if language == 'python':
                return cls._parse_python_file(file_path, content)
            else:
                return cls._parse_generic_file(file_path, content, language)
                
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            return []
    
    @classmethod
    def _parse_python_file(cls, file_path: str, content: str) -> List[CodeChunk]:
        """Parse Python file using AST"""
        chunks = []
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    chunk = cls._extract_function_chunk(node, lines, file_path)
                    if chunk:
                        chunks.append(chunk)
                
                elif isinstance(node, ast.ClassDef):
                    chunk = cls._extract_class_chunk(node, lines, file_path)
                    if chunk:
                        chunks.append(chunk)
                
                elif isinstance(node, ast.Import):
                    chunk = cls._extract_import_chunk(node, lines, file_path)
                    if chunk:
                        chunks.append(chunk)
                
                elif isinstance(node, ast.ImportFrom):
                    chunk = cls._extract_import_from_chunk(node, lines, file_path)
                    if chunk:
                        chunks.append(chunk)
        
        except SyntaxError:
            # Fallback to generic parsing if syntax error
            return cls._parse_generic_file(file_path, content, 'python')
        
        # If no chunks extracted, create file-level chunk
        if not chunks:
            chunks.append(CodeChunk(
                content=content,
                file_path=file_path,
                line_start=1,
                line_end=len(lines),
                language='python',
                chunk_type='file'
            ))
        
        return chunks
    
    @classmethod
    def _extract_function_chunk(cls, node: ast.FunctionDef, lines: List[str], file_path: str) -> Optional[CodeChunk]:
        """Extract function chunk"""
        try:
            start_line = node.lineno - 1  # Convert to 0-based
            end_line = node.end_lineno if node.end_lineno else len(lines)
            
            content = '\n'.join(lines[start_line:end_line])
            
            # Extract dependencies
            dependencies = []
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    dependencies.append(child.id)
            
            return CodeChunk(
                content=content,
                file_path=file_path,
                line_start=start_line + 1,
                line_end=end_line,
                language='python',
                chunk_type='function',
                name=node.name,
                dependencies=list(set(dependencies))
            )
        except Exception as e:
            logger.error(f"Error extracting function chunk: {str(e)}")
            return None
    
    @classmethod
    def _extract_class_chunk(cls, node: ast.ClassDef, lines: List[str], file_path: str) -> Optional[CodeChunk]:
        """Extract class chunk"""
        try:
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else len(lines)
            
            content = '\n'.join(lines[start_line:end_line])
            
            return CodeChunk(
                content=content,
                file_path=file_path,
                line_start=start_line + 1,
                line_end=end_line,
                language='python',
                chunk_type='class',
                name=node.name
            )
        except Exception as e:
            logger.error(f"Error extracting class chunk: {str(e)}")
            return None
    
    @classmethod
    def _extract_import_chunk(cls, node: ast.Import, lines: List[str], file_path: str) -> Optional[CodeChunk]:
        """Extract import chunk"""
        try:
            line = lines[node.lineno - 1]
            
            return CodeChunk(
                content=line.strip(),
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.lineno,
                language='python',
                chunk_type='import'
            )
        except Exception as e:
            logger.error(f"Error extracting import chunk: {str(e)}")
            return None
    
    @classmethod
    def _extract_import_from_chunk(cls, node: ast.ImportFrom, lines: List[str], file_path: str) -> Optional[CodeChunk]:
        """Extract import from chunk"""
        try:
            line = lines[node.lineno - 1]
            
            return CodeChunk(
                content=line.strip(),
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.lineno,
                language='python',
                chunk_type='import'
            )
        except Exception as e:
            logger.error(f"Error extracting import from chunk: {str(e)}")
            return None
    
    @classmethod
    def _parse_generic_file(cls, file_path: str, content: str, language: str) -> List[CodeChunk]:
        """Parse file using generic method for non-Python files"""
        chunks = []
        lines = content.split('\n')
        
        # Simple function/class detection using regex
        function_pattern = r'function\s+(\w+)|def\s+(\w+)|\w+\s+(\w+)\s*\([^)]*\)\s*{'
        class_pattern = r'class\s+(\w+)|interface\s+(\w+)|struct\s+(\w+)'
        
        for i, line in enumerate(lines):
            line_content = line.strip()
            if not line_content:
                continue
            
            # Check for function definition
            func_match = re.search(function_pattern, line_content)
            if func_match:
                func_name = next(g for g in func_match.groups() if g)
                chunks.append(CodeChunk(
                    content=line_content,
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    language=language,
                    chunk_type='function',
                    name=func_name
                ))
            
            # Check for class definition
            class_match = re.search(class_pattern, line_content)
            if class_match:
                class_name = next(g for g in class_match.groups() if g)
                chunks.append(CodeChunk(
                    content=line_content,
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    language=language,
                    chunk_type='class',
                    name=class_name
                ))
        
        # If no structured chunks found, create file-level chunk
        if not chunks:
            chunks.append(CodeChunk(
                content=content,
                file_path=file_path,
                line_start=1,
                line_end=len(lines),
                language=language,
                chunk_type='file'
            ))
        
        return chunks

class CodeIndexer:
    """Main code indexing class"""
    
    def __init__(self, vector_db_manager):
        self.vector_db_manager = vector_db_manager
        self.parser = CodeParser()
        self.indexed_files: Dict[str, FileIndex] = {}
        
    async def index_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Index all code files in a directory"""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                return {"error": f"Directory not found: {directory_path}"}
            
            # Find all code files
            code_files = self._find_code_files(directory, recursive, file_patterns)
            
            # Parse files in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                loop = asyncio.get_event_loop()
                tasks = []
                
                for file_path in code_files:
                    task = loop.run_in_executor(executor, self.parser.parse_file, str(file_path))
                    tasks.append(task)
                
                chunks_list = await asyncio.gather(*tasks)
            
            # Flatten chunks and create embeddings
            all_chunks = []
            for chunks in chunks_list:
                all_chunks.extend(chunks)
            
            # Create embeddings and store in vector database
            if all_chunks:
                await self._store_chunks_in_vector_db(all_chunks)
            
            # Update file index
            for i, file_path in enumerate(code_files):
                chunks = chunks_list[i]
                file_stat = os.stat(str(file_path))
                
                self.indexed_files[str(file_path)] = FileIndex(
                    file_path=str(file_path),
                    language=self.parser.get_language(str(file_path)) or 'unknown',
                    last_modified=file_stat.st_mtime,
                    chunks=chunks,
                    total_chunks=len(chunks),
                    file_size=file_stat.st_size
                )
            
            return {
                "indexed_files": len(code_files),
                "total_chunks": len(all_chunks),
                "languages": list(set(
                    self.parser.get_language(str(f)) for f in code_files
                    if self.parser.get_language(str(f))
                ))
            }
            
        except Exception as e:
            logger.error(f"Error indexing directory: {str(e)}")
            return {"error": str(e)}
    
    def _find_code_files(
        self,
        directory: Path,
        recursive: bool,
        file_patterns: Optional[List[str]]
    ) -> List[Path]:
        """Find all code files in directory"""
        code_files = []
        
        if file_patterns:
            patterns = file_patterns
        else:
            patterns = [f"*{ext}" for ext in self.parser.SUPPORTED_LANGUAGES.keys()]
        
        for pattern in patterns:
            if recursive:
                code_files.extend(directory.rglob(pattern))
            else:
                code_files.extend(directory.glob(pattern))
        
        # Remove duplicates and sort
        return sorted(list(set(code_files)))
    
    async def _store_chunks_in_vector_db(self, chunks: List[CodeChunk]):
        """Store chunks in vector database with embeddings"""
        try:
            # Prepare documents for vector database
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                # Create document content with metadata
                doc_content = f"{chunk.content}\n\nFile: {chunk.file_path}\nType: {chunk.chunk_type}"
                if chunk.name:
                    doc_content += f"\nName: {chunk.name}"
                
                documents.append(doc_content)
                
                # Create metadata
                metadata = {
                    "file_path": chunk.file_path,
                    "line_start": chunk.line_start,
                    "line_end": chunk.line_end,
                    "language": chunk.language,
                    "chunk_type": chunk.chunk_type,
                    "name": chunk.name or "",
                    "dependencies": chunk.dependencies
                }
                metadatas.append(metadata)
                
                # Create unique ID
                chunk_id = f"{Path(chunk.file_path).stem}_{chunk.chunk_type}_{i}"
                ids.append(chunk_id)
            
            # Add to vector database
            await self.vector_db_manager.add_documents(documents, metadatas, ids)
            
        except Exception as e:
            logger.error(f"Error storing chunks in vector DB: {str(e)}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for similar code chunks"""
        try:
            results = await self.vector_db_manager.similarity_search(query, k, threshold)
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    async def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a specific file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None
    
    async def update_file_index(self, file_path: str):
        """Update index for a specific file"""
        try:
            # Remove old chunks from vector database
            await self._remove_file_chunks(file_path)
            
            # Parse file again
            chunks = self.parser.parse_file(file_path)
            
            # Store new chunks
            await self._store_chunks_in_vector_db(chunks)
            
            # Update file index
            file_stat = os.stat(file_path)
            self.indexed_files[file_path] = FileIndex(
                file_path=file_path,
                language=self.parser.get_language(file_path) or 'unknown',
                last_modified=file_stat.st_mtime,
                chunks=chunks,
                total_chunks=len(chunks),
                file_size=file_stat.st_size
            )
            
        except Exception as e:
            logger.error(f"Error updating file index: {str(e)}")
    
    async def _remove_file_chunks(self, file_path: str):
        """Remove chunks for a file from vector database"""
        try:
            # Get all chunk IDs for this file
            chunk_ids = [
                f"{Path(file_path).stem}_{chunk.chunk_type}_{i}"
                for i, chunk in enumerate(self.indexed_files.get(file_path, FileIndex(
                    file_path=file_path, language='', last_modified=0, chunks=[], total_chunks=0, file_size=0
                )).chunks)
            ]
            
            if chunk_ids:
                await self.vector_db_manager.delete_documents(chunk_ids)
                
        except Exception as e:
            logger.error(f"Error removing file chunks: {str(e)}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        total_files = len(self.indexed_files)
        total_chunks = sum(info.total_chunks for info in self.indexed_files.values())
        languages = list(set(info.language for info in self.indexed_files.values()))
        
        return {
            "indexed_files": total_files,
            "total_chunks": total_chunks,
            "languages": languages,
            "file_types": {
                lang: sum(1 for info in self.indexed_files.values() if info.language == lang)
                for lang in languages
            }
        }