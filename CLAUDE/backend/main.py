#!/usr/bin/env python3
"""
CLAUDE Backend - Main Entry Point

Code-Library-Aware Unified Development Environment Backend
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from config.settings import settings
    from utils.helpers import setup_logging, ensure_directory_exists
    from api.server import app
    import uvicorn
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Set up logging
setup_logging(settings.log_level, settings.log_file)
logger = logging.getLogger(__name__)

class CLAUDEBackend:
    """Main CLAUDE backend application"""
    
    def __init__(self):
        self.app = app
        self.server = None
        self.should_shutdown = False
        
    async def startup(self):
        """Initialize the backend application"""
        logger.info("Starting CLAUDE Backend...")
        logger.info(f"Version: 0.1.0")
        logger.info(f"Environment: {settings}")
        
        # Ensure required directories exist
        ensure_directory_exists(settings.vector_db_path)
        ensure_directory_exists(settings.local_storage_path)
        ensure_directory_exists(Path(settings.log_file).parent)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("CLAUDE Backend initialized successfully")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.should_shutdown = True
    
    async def run(self):
        """Run the backend server"""
        try:
            await self.startup()
            
            # Start the server
            logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
            
            config = uvicorn.Config(
                app=self.app,
                host=settings.api_host,
                port=settings.api_port,
                reload=settings.api_reload,
                log_level=settings.log_level.lower()
            )
            
            self.server = uvicorn.Server(config)
            
            # Run the server
            await self.server.serve()
            
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt, shutting down...")
        except Exception as e:
            logger.error(f"Error running server: {str(e)}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown the backend application"""
        logger.info("Shutting down CLAUDE Backend...")
        
        if self.server:
            self.server.should_exit = True
        
        logger.info("CLAUDE Backend shutdown complete")

def main():
    """Main entry point"""
    backend = CLAUDEBackend()
    
    try:
        asyncio.run(backend.run())
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()