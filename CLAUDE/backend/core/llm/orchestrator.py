"""
LLM Orchestrator Module

This module handles all interactions with the local LLM (Ollama),
including prompt engineering, model management, and response generation.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
import asyncio
from dataclasses import dataclass

from ..config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    model: str
    usage: Dict[str, Any]
    metadata: Dict[str, Any]

class LLMOrchestrator:
    """Manages LLM interactions and prompt engineering"""
    
    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        self.model_name = model_name or settings.llm_model
        self.base_url = base_url or settings.ollama_base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        context: Optional[List[str]] = None
    ) -> LLMResponse:
        """
        Generate response from LLM with optional context
        """
        try:
            # Build the full prompt with context
            full_prompt = self._build_prompt(prompt, system_prompt, context)
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            # Make request to Ollama
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)  # 5 minutes
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"LLM API error: {response.status} - {error_text}")
                    raise Exception(f"LLM API request failed: {response.status}")
                
                result = await response.json()
                
                return LLMResponse(
                    content=result.get("response", ""),
                    model=self.model_name,
                    usage=result.get("usage", {}),
                    metadata=result.get("metadata", {})
                )
                
        except asyncio.TimeoutError:
            logger.error("LLM request timeout")
            raise Exception("LLM request timeout")
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise
    
    def _build_prompt(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[str]] = None
    ) -> str:
        """
        Build enhanced prompt with context and system instructions
        """
        prompt_parts = []
        
        # Add system prompt
        if system_prompt:
            prompt_parts.append(f"[SYSTEM INSTRUCTION]\n{system_prompt}\n")
        
        # Add context if provided
        if context:
            prompt_parts.append("[CODE CONTEXT]")
            for i, ctx in enumerate(context, 1):
                prompt_parts.append(f"Context {i}:\n{ctx}\n")
        
        # Add user prompt
        prompt_parts.append(f"[USER QUESTION]\n{user_prompt}\n")
        
        # Add response marker
        prompt_parts.append("[ANSWER]")
        
        return "\n".join(prompt_parts)
    
    async def generate_code(
        self,
        problem_description: str,
        code_context: Optional[List[str]] = None,
        style_guidelines: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate code with style awareness and context
        """
        system_prompt = self._get_code_generation_system_prompt(style_guidelines)
        
        return await self.generate_response(
            prompt=problem_description,
            system_prompt=system_prompt,
            context=code_context,
            temperature=0.3,  # Lower temperature for more consistent code
            max_tokens=2000
        )
    
    def _get_code_generation_system_prompt(self, style_guidelines: Optional[str] = None) -> str:
        """
        Generate system prompt for code generation
        """
        base_prompt = """You are a senior software engineer with expertise in multiple programming languages. 
Generate clean, efficient, and well-documented code that follows best practices.

Requirements:
- Write production-ready code with proper error handling
- Include necessary imports and dependencies
- Add appropriate comments explaining complex logic
- Follow the code style and patterns shown in the context
- Prioritize readability and maintainability
- Include type hints when applicable"""

        if style_guidelines:
            base_prompt += f"\n\nStyle Guidelines:\n{style_guidelines}"
        
        return base_prompt
    
    async def analyze_code_style(self, code_samples: List[str]) -> Dict[str, Any]:
        """
        Analyze code style from samples
        """
        analysis_prompt = """Analyze the following code samples and extract style patterns including:
- Naming conventions (variables, functions, classes)
- Indentation and formatting preferences
- Comment style and density
- Import organization
- Code structure patterns

Provide a concise summary of the style patterns observed."""

        context_samples = code_samples[:5]  # Limit to prevent context overflow
        
        response = await self.generate_response(
            prompt=analysis_prompt,
            context=context_samples,
            temperature=0.2
        )
        
        return {
            "style_analysis": response.content,
            "samples_analyzed": len(context_samples),
            "model_used": self.model_name
        }
    
    async def check_model_availability(self) -> bool:
        """
        Check if the specified model is available in Ollama
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models = await response.json()
                    available_models = [model["name"] for model in models.get("models", [])]
                    return self.model_name in available_models
                return False
        except Exception as e:
            logger.error(f"Error checking model availability: {str(e)}")
            return False
    
    async def pull_model(self) -> bool:
        """
        Pull the model if not available
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            logger.info(f"Pulling model: {self.model_name}")
            
            payload = {
                "name": self.model_name
            }
            
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=1800)  # 30 minutes
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")
            return False