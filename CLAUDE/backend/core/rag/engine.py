"""
RAG Engine Module

Implements Retrieval-Augmented Generation for context-aware code generation.
This module handles code retrieval, context building, and enhanced prompt generation.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
from pathlib import Path
import re

from ..llm.orchestrator import LLMOrchestrator, LLMResponse
from ..indexing.code_indexer import CodeIndexer
from ..style.style_analyzer import StyleAnalyzer
from ..config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class RetrievedCode:
    """Retrieved code chunk with metadata"""
    content: str
    file_path: str
    line_start: int
    line_end: int
    score: float
    language: str
    chunk_type: str  # "function", "class", "import", etc.

@dataclass
class RAGQuery:
    """Query for RAG system"""
    question: str
    language: Optional[str] = None
    context_type: Optional[str] = None  # "implementation", "explanation", "debug"
    max_context_chunks: int = 5
    similarity_threshold: float = 0.3

@dataclass
class RAGResult:
    """Result from RAG system"""
    answer: str
    retrieved_context: List[RetrievedCode]
    query: RAGQuery
    metadata: Dict[str, Any]

class RAGEngine:
    """Retrieval-Augmented Generation engine for code"""
    
    def __init__(
        self,
        code_indexer: CodeIndexer,
        style_analyzer: StyleAnalyzer,
        llm_orchestrator: LLMOrchestrator
    ):
        self.code_indexer = code_indexer
        self.style_analyzer = style_analyzer
        self.llm_orchestrator = llm_orchestrator
        
    async def query(
        self,
        query: RAGQuery,
        include_style_context: bool = True
    ) -> RAGResult:
        """
        Execute RAG query: retrieve context and generate enhanced response
        """
        try:
            # Step 1: Retrieve relevant code chunks
            retrieved_code = await self._retrieve_relevant_code(query)
            
            # Step 2: Build enhanced prompt with context
            context_text = self._build_context_text(retrieved_code)
            
            # Step 3: Get style guidelines if requested
            style_guidelines = None
            if include_style_context:
                style_guidelines = await self.style_analyzer.get_style_guidelines()
            
            # Step 4: Generate enhanced response
            enhanced_prompt = self._build_enhanced_prompt(query.question, context_text)
            
            response = await self.llm_orchestrator.generate_code(
                problem_description=enhanced_prompt,
                code_context=[ctx.content for ctx in retrieved_code],
                style_guidelines=style_guidelines
            )
            
            return RAGResult(
                answer=response.content,
                retrieved_context=retrieved_code,
                query=query,
                metadata={
                    "model_used": response.model,
                    "usage": response.usage,
                    "style_context_included": include_style_context,
                    "retrieved_chunks_count": len(retrieved_code)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in RAG query: {str(e)}")
            raise
    
    async def _retrieve_relevant_code(self, query: RAGQuery) -> List[RetrievedCode]:
        """
        Retrieve relevant code chunks based on query
        """
        try:
            # Build search query with language context
            search_query = query.question
            if query.language:
                search_query += f" {query.language}"
            
            # Retrieve from vector database
            results = await self.code_indexer.similarity_search(
                query=search_query,
                k=query.max_context_chunks,
                threshold=query.similarity_threshold
            )
            
            # Convert to RetrievedCode objects
            retrieved_code = []
            for result in results:
                retrieved_code.append(RetrievedCode(
                    content=result["content"],
                    file_path=result["metadata"]["file_path"],
                    line_start=result["metadata"]["line_start"],
                    line_end=result["metadata"]["line_end"],
                    score=result["score"],
                    language=result["metadata"]["language"],
                    chunk_type=result["metadata"]["chunk_type"]
                ))
            
            # Sort by relevance score
            retrieved_code.sort(key=lambda x: x.score, reverse=True)
            
            return retrieved_code
            
        except Exception as e:
            logger.error(f"Error retrieving code: {str(e)}")
            return []
    
    def _build_context_text(self, retrieved_code: List[RetrievedCode]) -> str:
        """
        Build formatted context text from retrieved code chunks
        """
        if not retrieved_code:
            return ""
        
        context_parts = []
        context_parts.append("Relevant code from your codebase:")
        
        for i, code in enumerate(retrieved_code, 1):
            context_parts.append(f"\n--- Code Snippet {i} ---")
            context_parts.append(f"File: {code.file_path} (lines {code.line_start}-{code.line_end})")
            context_parts.append(f"Language: {code.language} | Type: {code.chunk_type}")
            context_parts.append(f"Relevance Score: {code.score:.3f}")
            context_parts.append("```")
            context_parts.append(code.content)
            context_parts.append("```")
        
        return "\n".join(context_parts)
    
    def _build_enhanced_prompt(self, user_question: str, context_text: str) -> str:
        """
        Build enhanced prompt with retrieved context
        """
        enhanced_prompt = user_question
        
        if context_text:
            enhanced_prompt = f"""
{user_question}

{context_text}

Please use the relevant code snippets above as context and reference for your solution.
Prioritize using similar patterns, functions, and classes from the codebase when applicable.
"""
        
        return enhanced_prompt
    
    async def explain_code(
        self,
        code_snippet: str,
        language: Optional[str] = None
    ) -> RAGResult:
        """
        Explain a code snippet with context from the codebase
        """
        query = RAGQuery(
            question=f"Explain this code: {code_snippet}",
            language=language,
            context_type="explanation",
            max_context_chunks=3
        )
        
        return await self.query(query)
    
    async def debug_code(
        self,
        code_snippet: str,
        error_message: Optional[str] = None,
        language: Optional[str] = None
    ) -> RAGResult:
        """
        Debug code with context from the codebase
        """
        debug_query = f"Debug this code: {code_snippet}"
        if error_message:
            debug_query += f"\nError: {error_message}"
        
        query = RAGQuery(
            question=debug_query,
            language=language,
            context_type="debug",
            max_context_chunks=5
        )
        
        return await self.query(query)
    
    async def generate_implementation(
        self,
        requirements: str,
        language: Optional[str] = None,
        framework: Optional[str] = None
    ) -> RAGResult:
        """
        Generate implementation based on requirements
        """
        impl_query = requirements
        if language:
            impl_query += f"\nLanguage: {language}"
        if framework:
            impl_query += f"\nFramework: {framework}"
        
        query = RAGQuery(
            question=impl_query,
            language=language,
            context_type="implementation",
            max_context_chunks=7
        )
        
        return await self.query(query)
    
    async def suggest_improvements(
        self,
        code_snippet: str,
        language: Optional[str] = None
    ) -> RAGResult:
        """
        Suggest improvements for existing code
        """
        query = RAGQuery(
            question=f"Suggest improvements for this code: {code_snippet}",
            language=language,
            context_type="improvement",
            max_context_chunks=5
        )
        
        return await self.query(query)
    
    async def get_code_context_summary(
        self,
        file_path: str,
        line_number: int,
        context_radius: int = 10
    ) -> Dict[str, Any]:
        """
        Get code context around a specific line number
        """
        try:
            # Get file content
            file_content = await self.code_indexer.get_file_content(file_path)
            if not file_content:
                return {"error": "File not found"}
            
            lines = file_content.split('\n')
            start_line = max(0, line_number - context_radius)
            end_line = min(len(lines), line_number + context_radius)
            
            context_lines = lines[start_line:end_line]
            
            return {
                "file_path": file_path,
                "line_number": line_number,
                "context_start": start_line + 1,
                "context_end": end_line,
                "context": '\n'.join(context_lines),
                "total_lines": len(lines)
            }
            
        except Exception as e:
            logger.error(f"Error getting code context: {str(e)}")
            return {"error": str(e)}