from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # LLM Configuration
    llm_model: str = "codellama:7b"
    ollama_base_url: str = "http://localhost:11434"
    
    # Vector Database
    vector_db_path: str = "./data/vector_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Storage
    storage_type: str = "local"
    local_storage_path: str = "./data"
    cloud_storage_bucket: Optional[str] = None
    
    # API Configuration
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_reload: bool = True
    
    # Monitoring
    enable_file_watcher: bool = True
    watch_directories: List[str] = ["./test_codebase"]
    git_integration: bool = True
    
    # Fine-tuning
    enable_finetuning: bool = False
    finetuning_data_path: str = "./data/finetuning"
    model_adapters_path: str = "./data/adapters"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/claude.log"
    
    class Config:
        env_file = ".env"

settings = Settings()