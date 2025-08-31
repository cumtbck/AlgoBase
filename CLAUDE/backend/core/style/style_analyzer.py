"""
Style Analyzer Module

Analyzes code style patterns from the codebase and provides style guidelines
for consistent code generation.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import asyncio
from pathlib import Path

from ..indexing.code_indexer import CodeIndexer, CodeChunk
from ..llm.orchestrator import LLMOrchestrator
from ..config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class StylePattern:
    """Represents a detected style pattern"""
    pattern_type: str
    pattern_value: str
    frequency: int
    examples: List[str]
    confidence: float

@dataclass
class StyleGuidelines:
    """Comprehensive style guidelines for code generation"""
    naming_conventions: Dict[str, str]
    formatting_rules: Dict[str, Any]
    comment_style: Dict[str, str]
    import_organization: str
    error_handling_patterns: List[str]
    documentation_standards: Dict[str, str]
    language_specific: Dict[str, Any]
    overall_style_profile: str

class CodeStyleAnalyzer:
    """Analyzes code style patterns from indexed code"""
    
    def __init__(self, code_indexer: CodeIndexer, llm_orchestrator: LLMOrchestrator):
        self.code_indexer = code_indexer
        self.llm_orchestrator = llm_orchestrator
        self.style_cache: Dict[str, StyleGuidelines] = {}
        
    async def analyze_codebase_style(self, force_refresh: bool = False) -> StyleGuidelines:
        """Analyze style patterns from the entire codebase"""
        cache_key = "codebase_style"
        
        if not force_refresh and cache_key in self.style_cache:
            return self.style_cache[cache_key]
        
        try:
            # Get all indexed chunks
            all_chunks = []
            for file_index in self.code_indexer.indexed_files.values():
                all_chunks.extend(file_index.chunks)
            
            if not all_chunks:
                logger.warning("No code chunks found for style analysis")
                return self._get_default_style_guidelines()
            
            # Analyze different aspects of code style
            naming_patterns = self._analyze_naming_conventions(all_chunks)
            formatting_patterns = self._analyze_formatting_patterns(all_chunks)
            comment_patterns = self._analyze_comment_patterns(all_chunks)
            import_patterns = self._analyze_import_patterns(all_chunks)
            error_patterns = self._analyze_error_handling_patterns(all_chunks)
            doc_patterns = self._analyze_documentation_patterns(all_chunks)
            
            # Group by language
            language_specific = self._analyze_language_specific_patterns(all_chunks)
            
            # Generate overall style profile
            style_profile = await self._generate_style_profile(all_chunks)
            
            guidelines = StyleGuidelines(
                naming_conventions=naming_patterns,
                formatting_rules=formatting_patterns,
                comment_style=comment_patterns,
                import_organization=import_patterns,
                error_handling_patterns=error_patterns,
                documentation_standards=doc_patterns,
                language_specific=language_specific,
                overall_style_profile=style_profile
            )
            
            # Cache the result
            self.style_cache[cache_key] = guidelines
            
            return guidelines
            
        except Exception as e:
            logger.error(f"Error analyzing codebase style: {str(e)}")
            return self._get_default_style_guidelines()
    
    def _analyze_naming_conventions(self, chunks: List[CodeChunk]) -> Dict[str, str]:
        """Analyze naming conventions used in the codebase"""
        naming_patterns = {
            'variables': Counter(),
            'functions': Counter(),
            'classes': Counter(),
            'constants': Counter()
        }
        
        for chunk in chunks:
            if chunk.language != 'python':
                continue
                
            # Extract function names
            if chunk.chunk_type == 'function' and chunk.name:
                naming_patterns['functions'][self._classify_naming_style(chunk.name)] += 1
            
            # Extract class names
            elif chunk.chunk_type == 'class' and chunk.name:
                naming_patterns['classes'][self._classify_naming_style(chunk.name)] += 1
            
            # Extract variable names and constants from content
            elif chunk.chunk_type in ['function', 'class']:
                variables, constants = self._extract_variables_and_constants(chunk.content)
                for var in variables:
                    naming_patterns['variables'][self._classify_naming_style(var)] += 1
                for const in constants:
                    naming_patterns['constants'][self._classify_naming_style(const)] += 1
        
        # Determine most common convention for each type
        result = {}
        for category, patterns in naming_patterns.items():
            if patterns:
                most_common = patterns.most_common(1)[0][0]
                result[category] = most_common
            else:
                result[category] = 'unknown'
        
        return result
    
    def _classify_naming_style(self, name: str) -> str:
        """Classify the naming style of a given name"""
        if name.isupper():
            return 'UPPER_CASE'
        elif name[0].isupper() and '_' not in name:
            return 'PascalCase'
        elif name.islower() and '_' in name:
            return 'snake_case'
        elif name[0].islower() and '_' not in name:
            return 'camelCase'
        else:
            return 'mixed'
    
    def _extract_variables_and_constants(self, content: str) -> Tuple[List[str], List[str]]:
        """Extract variable and constant names from code content"""
        variables = []
        constants = []
        
        # Simple regex patterns for Python
        var_pattern = r'\b([a-z_][a-z0-9_]*)\s*='
        const_pattern = r'\b([A-Z_][A-Z0-9_]*)\s*='
        
        var_matches = re.findall(var_pattern, content)
        const_matches = re.findall(const_pattern, content)
        
        # Filter out keywords and common patterns
        keywords = {'if', 'for', 'while', 'with', 'def', 'class', 'import', 'from'}
        variables = [v for v in var_matches if v not in keywords and len(v) > 1]
        constants = [c for c in const_matches if c not in keywords and len(c) > 1]
        
        return variables, constants
    
    def _analyze_formatting_patterns(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analyze formatting patterns like indentation, spacing, etc."""
        patterns = {
            'indentation_style': Counter(),
            'line_length': [],
            'spacing_around_operators': Counter(),
            'bracket_style': Counter()
        }
        
        for chunk in chunks:
            lines = chunk.content.split('\n')
            
            for line in lines:
                # Analyze indentation
                if line.startswith(' '):
                    indent_size = len(line) - len(line.lstrip())
                    if indent_size % 4 == 0:
                        patterns['indentation_style']['spaces_4'] += 1
                    elif indent_size % 2 == 0:
                        patterns['indentation_style']['spaces_2'] += 1
                elif line.startswith('\t'):
                    patterns['indentation_style']['tabs'] += 1
                
                # Analyze line length
                patterns['line_length'].append(len(line))
                
                # Analyze spacing around operators
                if '=' in line and not line.strip().startswith('#'):
                    if ' = ' in line:
                        patterns['spacing_around_operators']['spaced'] += 1
                    else:
                        patterns['spacing_around_operators']['unspaced'] += 1
        
        # Process results
        result = {
            'indentation': patterns['indentation_style'].most_common(1)[0][0] if patterns['indentation_style'] else 'unknown',
            'average_line_length': sum(patterns['line_length']) / len(patterns['line_length']) if patterns['line_length'] else 0,
            'max_line_length': max(patterns['line_length']) if patterns['line_length'] else 0,
            'operator_spacing': patterns['spacing_around_operators'].most_common(1)[0][0] if patterns['spacing_around_operators'] else 'unknown'
        }
        
        return result
    
    def _analyze_comment_patterns(self, chunks: List[CodeChunk]) -> Dict[str, str]:
        """Analyze comment style and density"""
        comment_patterns = {
            'inline_comments': 0,
            'block_comments': 0,
            'docstrings': 0,
            'total_lines': 0,
            'comment_lines': 0
        }
        
        for chunk in chunks:
            lines = chunk.content.split('\n')
            comment_patterns['total_lines'] += len(lines)
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#'):
                    comment_patterns['comment_lines'] += 1
                    if len(stripped) > 1 and stripped[1] == ' ':
                        comment_patterns['inline_comments'] += 1
                
                # Check for docstrings (simplified)
                if '"""' in line or "'''" in line:
                    comment_patterns['docstrings'] += 1
        
        # Calculate comment density
        density = comment_patterns['comment_lines'] / comment_patterns['total_lines'] if comment_patterns['total_lines'] > 0 else 0
        
        return {
            'comment_density': 'high' if density > 0.2 else 'medium' if density > 0.1 else 'low',
            'comment_style': 'detailed' if comment_patterns['docstrings'] > 0 else 'simple'
        }
    
    def _analyze_import_patterns(self, chunks: List[CodeChunk]) -> str:
        """Analyze import organization patterns"""
        import_styles = Counter()
        
        for chunk in chunks:
            if chunk.chunk_type == 'import':
                content = chunk.content
                
                if 'import ' in content and ' as ' in content:
                    import_styles['with_alias'] += 1
                elif 'from ' in content and ' import ' in content:
                    import_styles['from_import'] += 1
                else:
                    import_styles['direct_import'] += 1
        
        return import_styles.most_common(1)[0][0] if import_styles else 'mixed'
    
    def _analyze_error_handling_patterns(self, chunks: List[CodeChunk]) -> List[str]:
        """Analyze error handling patterns"""
        error_patterns = []
        
        for chunk in chunks:
            if chunk.language != 'python':
                continue
                
            content = chunk.content
            
            # Check for try-except blocks
            if 'try:' in content and 'except' in content:
                error_patterns.append('try_except')
            
            # Check for raise statements
            if 'raise ' in content:
                error_patterns.append('raise_statements')
            
            # Check for assertions
            if 'assert ' in content:
                error_patterns.append('assertions')
        
        return list(set(error_patterns))
    
    def _analyze_documentation_patterns(self, chunks: List[CodeChunk]) -> Dict[str, str]:
        """Analyze documentation patterns"""
        doc_patterns = {
            'functions_with_docstrings': 0,
            'classes_with_docstrings': 0,
            'total_functions': 0,
            'total_classes': 0
        }
        
        for chunk in chunks:
            if chunk.language != 'python':
                continue
                
            if chunk.chunk_type == 'function':
                doc_patterns['total_functions'] += 1
                if '"""' in chunk.content or "'''" in chunk.content:
                    doc_patterns['functions_with_docstrings'] += 1
            
            elif chunk.chunk_type == 'class':
                doc_patterns['total_classes'] += 1
                if '"""' in chunk.content or "'''" in chunk.content:
                    doc_patterns['classes_with_docstrings'] += 1
        
        # Calculate documentation coverage
        func_coverage = (doc_patterns['functions_with_docstrings'] / 
                        doc_patterns['total_functions']) if doc_patterns['total_functions'] > 0 else 0
        
        class_coverage = (doc_patterns['classes_with_docstrings'] / 
                         doc_patterns['total_classes']) if doc_patterns['total_classes'] > 0 else 0
        
        return {
            'function_documentation_coverage': 'high' if func_coverage > 0.8 else 'medium' if func_coverage > 0.5 else 'low',
            'class_documentation_coverage': 'high' if class_coverage > 0.8 else 'medium' if class_coverage > 0.5 else 'low'
        }
    
    def _analyze_language_specific_patterns(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analyze language-specific patterns"""
        language_patterns = defaultdict(dict)
        
        for chunk in chunks:
            lang = chunk.language
            if lang not in language_patterns:
                language_patterns[lang] = {}
            
            # Language-specific analysis
            if lang == 'python':
                language_patterns[lang] = self._analyze_python_patterns(chunk)
            elif lang in ['javascript', 'typescript']:
                language_patterns[lang] = self._analyze_js_patterns(chunk)
        
        return dict(language_patterns)
    
    def _analyze_python_patterns(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Analyze Python-specific patterns"""
        patterns = {
            'type_hints': 'type hints' in chunk.content.lower(),
            'f_strings': 'f"' in chunk.content or "f'" in chunk.content,
            'list_comprehensions': '[' in chunk.content and 'for' in chunk.content and ']' in chunk.content,
            'decorators': '@' in chunk.content
        }
        return patterns
    
    def _analyze_js_patterns(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript-specific patterns"""
        patterns = {
            'arrow_functions': '=>' in chunk.content,
            'template_literals': '`' in chunk.content,
            'destructuring': '{' in chunk.content and '}' in chunk.content and '=' in chunk.content,
            'async_await': 'async' in chunk.content or 'await' in chunk.content
        }
        return patterns
    
    async def _generate_style_profile(self, chunks: List[CodeChunk]) -> str:
        """Generate overall style profile using LLM"""
        try:
            # Select representative samples
            sample_chunks = chunks[:10]  # Limit context size
            sample_code = [chunk.content for chunk in sample_chunks]
            
            analysis_prompt = """Analyze the following code samples and provide a concise summary of the overall coding style and patterns. Focus on:
1. Overall code organization and structure
2. Naming conventions and patterns
3. Code complexity and readability
4. Best practices followed
5. Any distinctive style characteristics

Provide a 2-3 sentence summary that captures the essence of this codebase's style."""
            
            response = await self.llm_orchestrator.generate_response(
                prompt=analysis_prompt,
                context=sample_code,
                temperature=0.3
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating style profile: {str(e)}")
            return "Unable to generate style profile"
    
    def _get_default_style_guidelines(self) -> StyleGuidelines:
        """Return default style guidelines when analysis fails"""
        return StyleGuidelines(
            naming_conventions={
                'variables': 'snake_case',
                'functions': 'snake_case',
                'classes': 'PascalCase',
                'constants': 'UPPER_CASE'
            },
            formatting_rules={
                'indentation': 'spaces_4',
                'average_line_length': 80,
                'max_line_length': 120,
                'operator_spacing': 'spaced'
            },
            comment_style={
                'comment_density': 'medium',
                'comment_style': 'simple'
            },
            import_organization='direct_import',
            error_handling_patterns=['try_except'],
            documentation_standards={
                'function_documentation_coverage': 'medium',
                'class_documentation_coverage': 'medium'
            },
            language_specific={},
            overall_style_profile='Standard Python code style'
        )
    
    async def get_style_guidelines(self, language: Optional[str] = None) -> str:
        """Get formatted style guidelines for code generation"""
        guidelines = await self.analyze_codebase_style()
        
        guidelines_text = f"""
Code Style Guidelines:
- Naming: Variables use {guidelines.naming_conventions.get('variables', 'snake_case')}, 
  Functions use {guidelines.naming_conventions.get('functions', 'snake_case')}, 
  Classes use {guidelines.naming_conventions.get('classes', 'PascalCase')}
- Formatting: {guidelines.formatting_rules.get('indentation', 'spaces_4')} indentation, 
  Average line length: {guidelines.formatting_rules.get('average_line_length', 80)} characters
- Comments: {guidelines.comment_style.get('comment_density', 'medium')} density, 
  {guidelines.comment_style.get('comment_style', 'simple')} style
- Imports: {guidelines.import_organization}
- Error handling: {', '.join(guidelines.error_handling_patterns)}

Overall style profile: {guidelines.overall_style_profile}
"""
        
        return guidelines_text.strip()
    
    async def analyze_file_style(self, file_path: str) -> Dict[str, Any]:
        """Analyze style patterns for a specific file"""
        try:
            # Get chunks for this file
            file_index = self.code_indexer.indexed_files.get(file_path)
            if not file_index:
                return {"error": "File not indexed"}
            
            # Analyze patterns
            naming_patterns = self._analyze_naming_conventions(file_index.chunks)
            formatting_patterns = self._analyze_formatting_patterns(file_index.chunks)
            comment_patterns = self._analyze_comment_patterns(file_index.chunks)
            
            return {
                "file_path": file_path,
                "language": file_index.language,
                "naming_conventions": naming_patterns,
                "formatting_patterns": formatting_patterns,
                "comment_patterns": comment_patterns,
                "total_chunks": file_index.total_chunks
            }
            
        except Exception as e:
            logger.error(f"Error analyzing file style: {str(e)}")
            return {"error": str(e)}