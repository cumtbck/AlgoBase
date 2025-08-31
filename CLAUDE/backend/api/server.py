"""
API Server Module

FastAPI server providing REST API endpoints for CLAUDE application.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..core.llm.orchestrator import LLMOrchestrator, LLMResponse
from ..core.rag.engine import RAGEngine, RAGQuery, RAGResult
from ..core.indexing.code_indexer import CodeIndexer
from ..core.style.style_analyzer import CodeStyleAnalyzer
from ..storage.vector.vector_db import VectorDatabaseManager
from ..storage.storage_manager import StorageManager
from ..monitoring.filewatch.file_watcher import MonitoringManager, FileChangeEvent
from ..config.settings import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Pydantic models for API
class QueryRequest(BaseModel):
    question: str = Field(..., description="User question or request")
    language: Optional[str] = Field(None, description="Programming language context")
    context_type: Optional[str] = Field(None, description="Type of context needed")
    max_context_chunks: int = Field(5, description="Maximum context chunks to retrieve")
    similarity_threshold: float = Field(0.3, description="Similarity threshold for retrieval")

class IndexRequest(BaseModel):
    directory_path: str = Field(..., description="Path to directory to index")
    recursive: bool = Field(True, description="Whether to index recursively")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to include")

class CodeGenerationRequest(BaseModel):
    problem_description: str = Field(..., description="Description of the problem to solve")
    language: Optional[str] = Field(None, description="Target programming language")
    framework: Optional[str] = Field(None, description="Target framework")

class StyleAnalysisRequest(BaseModel):
    file_path: Optional[str] = Field(None, description="Specific file to analyze")
    force_refresh: bool = Field(False, description="Force refresh of cached analysis")

class MonitoringStatus(BaseModel):
    is_running: bool
    watched_directories: List[str]
    file_change_count: int
    last_activity: Optional[str]

class SystemStatus(BaseModel):
    status: str
    components: Dict[str, Any]
    uptime: float
    version: str

# Global variables for components
vector_db: Optional[VectorDatabaseManager] = None
storage_manager: Optional[StorageManager] = None
code_indexer: Optional[CodeIndexer] = None
style_analyzer: Optional[CodeStyleAnalyzer] = None
llm_orchestrator: Optional[LLMOrchestrator] = None
rag_engine: Optional[RAGEngine] = None
monitoring_manager: Optional[MonitoringManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global vector_db, storage_manager, code_indexer, style_analyzer
    global llm_orchestrator, rag_engine, monitoring_manager
    
    logger.info("Starting CLAUDE API server...")
    
    try:
        # Initialize components
        vector_db = VectorDatabaseManager()
        storage_manager = StorageManager()
        llm_orchestrator = LLMOrchestrator()
        
        # Initialize core components
        code_indexer = CodeIndexer(vector_db)
        style_analyzer = CodeStyleAnalyzer(code_indexer, llm_orchestrator)
        rag_engine = RAGEngine(code_indexer, style_analyzer, llm_orchestrator)
        
        # Initialize monitoring
        monitoring_manager = MonitoringManager(settings.watch_directories[0] if settings.watch_directories else ".")
        
        # Set up file change callback
        async def handle_file_change(event: FileChangeEvent):
            """Handle file change events"""
            if event.event_type in ["modified", "created"]:
                logger.info(f"Re-indexing modified file: {event.file_path}")
                try:
                    await code_indexer.update_file_index(event.file_path)
                except Exception as e:
                    logger.error(f"Error re-indexing file {event.file_path}: {str(e)}")
        
        monitoring_manager.add_change_callback(handle_file_change)
        
        # Start monitoring if enabled
        if settings.enable_file_watcher:
            monitoring_manager.start_monitoring()
        
        logger.info("CLAUDE API server initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Error initializing CLAUDE components: {str(e)}")
        raise
    
    finally:
        # Cleanup
        if monitoring_manager:
            monitoring_manager.stop_monitoring()
        if vector_db:
            await vector_db.close()
        logger.info("CLAUDE API server shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="CLAUDE API",
    description="Code-Library-Aware Unified Development Environment API",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "CLAUDE API Server", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

@app.post("/query", response_model=Dict[str, Any])
async def query_rag(request: QueryRequest):
    """Execute RAG query"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        query = RAGQuery(
            question=request.question,
            language=request.language,
            context_type=request.context_type,
            max_context_chunks=request.max_context_chunks,
            similarity_threshold=request.similarity_threshold
        )
        
        result = await rag_engine.query(query)
        
        return {
            "answer": result.answer,
            "retrieved_context": [
                {
                    "content": ctx.content,
                    "file_path": ctx.file_path,
                    "line_start": ctx.line_start,
                    "line_end": ctx.line_end,
                    "score": ctx.score,
                    "language": ctx.language,
                    "chunk_type": ctx.chunk_type
                }
                for ctx in result.retrieved_context
            ],
            "metadata": result.metadata
        }
        
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-code", response_model=Dict[str, Any])
async def generate_code(request: CodeGenerationRequest):
    """Generate code with context awareness"""
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        result = await rag_engine.generate_implementation(
            requirements=request.problem_description,
            language=request.language,
            framework=request.framework
        )
        
        return {
            "generated_code": result.answer,
            "retrieved_context": [
                {
                    "content": ctx.content,
                    "file_path": ctx.file_path,
                    "score": ctx.score
                }
                for ctx in result.retrieved_context
            ],
            "metadata": result.metadata
        }
        
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index/directory", response_model=Dict[str, Any])
async def index_directory(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index a directory for code search"""
    if not code_indexer:
        raise HTTPException(status_code=503, detail="Code indexer not initialized")
    
    try:
        # Run indexing in background
        async def run_indexing():
            result = await code_indexer.index_directory(
                request.directory_path,
                request.recursive,
                request.file_patterns
            )
            logger.info(f"Directory indexing completed: {result}")
        
        background_tasks.add_task(run_indexing)
        
        return {
            "message": "Directory indexing started",
            "directory_path": request.directory_path,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error starting directory indexing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/index/stats")
async def get_index_stats():
    """Get indexing statistics"""
    if not code_indexer:
        raise HTTPException(status_code=503, detail="Code indexer not initialized")
    
    try:
        stats = code_indexer.get_index_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting index stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/style/analyze", response_model=Dict[str, Any])
async def analyze_style(request: StyleAnalysisRequest):
    """Analyze code style"""
    if not style_analyzer:
        raise HTTPException(status_code=503, detail="Style analyzer not initialized")
    
    try:
        if request.file_path:
            result = await style_analyzer.analyze_file_style(request.file_path)
        else:
            guidelines = await style_analyzer.analyze_codebase_style(request.force_refresh)
            result = {
                "guidelines": {
                    "naming_conventions": guidelines.naming_conventions,
                    "formatting_rules": guidelines.formatting_rules,
                    "comment_style": guidelines.comment_style,
                    "import_organization": guidelines.import_organization,
                    "error_handling_patterns": guidelines.error_handling_patterns,
                    "documentation_standards": guidelines.documentation_standards,
                    "overall_style_profile": guidelines.overall_style_profile
                }
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing style: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/style/guidelines")
async def get_style_guidelines():
    """Get current style guidelines"""
    if not style_analyzer:
        raise HTTPException(status_code=503, detail="Style analyzer not initialized")
    
    try:
        guidelines = await style_analyzer.get_style_guidelines()
        return {"guidelines": guidelines}
        
    except Exception as e:
        logger.error(f"Error getting style guidelines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/status")
async def get_monitoring_status():
    """Get monitoring status"""
    if not monitoring_manager:
        raise HTTPException(status_code=503, detail="Monitoring manager not initialized")
    
    try:
        stats = monitoring_manager.get_monitoring_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/start")
async def start_monitoring():
    """Start file monitoring"""
    if not monitoring_manager:
        raise HTTPException(status_code=503, detail="Monitoring manager not initialized")
    
    try:
        monitoring_manager.start_monitoring()
        return {"message": "Monitoring started"}
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/stop")
async def stop_monitoring():
    """Stop file monitoring"""
    if not monitoring_manager:
        raise HTTPException(status_code=503, detail="Monitoring manager not initialized")
    
    try:
        monitoring_manager.stop_monitoring()
        return {"message": "Monitoring stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/add-directory")
async def add_watch_directory(directory_path: str):
    """Add directory to watch list"""
    if not monitoring_manager:
        raise HTTPException(status_code=503, detail="Monitoring manager not initialized")
    
    try:
        monitoring_manager.add_watch_directory(directory_path)
        return {"message": f"Added directory to watch list: {directory_path}"}
        
    except Exception as e:
        logger.error(f"Error adding watch directory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage/stats")
async def get_storage_stats():
    """Get storage statistics"""
    if not storage_manager:
        raise HTTPException(status_code=503, detail="Storage manager not initialized")
    
    try:
        stats = await storage_manager.get_storage_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage/backup")
async def backup_storage(backup_path: str):
    """Create storage backup"""
    if not storage_manager:
        raise HTTPException(status_code=503, detail="Storage manager not initialized")
    
    try:
        result = await storage_manager.backup_data(backup_path)
        return result
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage/restore")
async def restore_storage(backup_path: str):
    """Restore storage from backup"""
    if not storage_manager:
        raise HTTPException(status_code=503, detail="Storage manager not initialized")
    
    try:
        result = await storage_manager.restore_data(backup_path)
        return result
        
    except Exception as e:
        logger.error(f"Error restoring from backup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vector-db/stats")
async def get_vector_db_stats():
    """Get vector database statistics"""
    if not vector_db:
        raise HTTPException(status_code=503, detail="Vector database not initialized")
    
    try:
        stats = await vector_db.get_collection_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting vector DB stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vector-db/clear")
async def clear_vector_db():
    """Clear vector database"""
    if not vector_db:
        raise HTTPException(status_code=503, detail="Vector database not initialized")
    
    try:
        result = await vector_db.clear_collection()
        return result
        
    except Exception as e:
        logger.error(f"Error clearing vector DB: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/status")
async def get_system_status():
    """Get comprehensive system status"""
    try:
        components = {}
        
        # Check each component
        components["vector_db"] = vector_db is not None
        components["storage_manager"] = storage_manager is not None
        components["code_indexer"] = code_indexer is not None
        components["style_analyzer"] = style_analyzer is not None
        components["llm_orchestrator"] = llm_orchestrator is not None
        components["rag_engine"] = rag_engine is not None
        components["monitoring_manager"] = monitoring_manager is not None
        
        # Check if monitoring is running
        monitoring_active = False
        if monitoring_manager:
            monitoring_stats = monitoring_manager.get_monitoring_stats()
            monitoring_active = monitoring_stats.get("file_watcher", {}).get("is_running", False)
        
        return {
            "status": "healthy" if all(components.values()) else "degraded",
            "components": components,
            "monitoring_active": monitoring_active,
            "version": "0.1.0",
            "uptime": 0  # TODO: Track actual uptime
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm/check-availability")
async def check_llm_availability():
    """Check if LLM is available"""
    if not llm_orchestrator:
        raise HTTPException(status_code=503, detail="LLM orchestrator not initialized")
    
    try:
        available = await llm_orchestrator.check_model_availability()
        return {"available": available, "model": settings.llm_model}
        
    except Exception as e:
        logger.error(f"Error checking LLM availability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/llm/pull-model")
async def pull_llm_model():
    """Pull LLM model"""
    if not llm_orchestrator:
        raise HTTPException(status_code=503, detail="LLM orchestrator not initialized")
    
    try:
        success = await llm_orchestrator.pull_model()
        return {"success": success, "model": settings.llm_model}
        
    except Exception as e:
        logger.error(f"Error pulling LLM model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )