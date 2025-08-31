"""
Vector Database Manager

Manages vector database operations for code embeddings using ChromaDB.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from dataclasses import dataclass

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from ..config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a search result from vector database"""
    content: str
    metadata: Dict[str, Any]
    score: float
    id: str

class VectorDatabaseManager:
    """Manages vector database operations"""
    
    def __init__(self, db_path: Optional[str] = None, embedding_model: Optional[str] = None):
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB and sentence-transformers are required for vector database functionality")
        
        self.db_path = db_path or settings.vector_db_path
        self.embedding_model_name = embedding_model or settings.embedding_model
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="code_chunks",
            metadata={"description": "Code chunks for RAG system"}
        )
        
        logger.info(f"Vector database initialized at {self.db_path}")
        logger.info(f"Using embedding model: {self.embedding_model_name}")
    
    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> Dict[str, Any]:
        """Add documents to vector database with embeddings"""
        try:
            if len(documents) != len(metadatas) or len(documents) != len(ids):
                raise ValueError("Documents, metadatas, and ids must have the same length")
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} documents")
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(documents)} documents to vector database")
            
            return {
                "added_count": len(documents),
                "collection_name": "code_chunks",
                "total_documents": self.collection.count()
            }
            
        except Exception as e:
            logger.error(f"Error adding documents to vector database: {str(e)}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            search_results = []
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i]
                score = 1.0 / (1.0 + distance)  # Convert distance to similarity score
                
                # Apply threshold
                if score >= threshold:
                    search_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": score,
                        "id": results["ids"][0][i]
                    })
            
            # Sort by score
            search_results.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Found {len(search_results)} results for query: {query[:50]}...")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    async def delete_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """Delete documents from vector database"""
        try:
            self.collection.delete(ids=document_ids)
            
            logger.info(f"Deleted {len(document_ids)} documents from vector database")
            
            return {
                "deleted_count": len(document_ids),
                "remaining_documents": self.collection.count()
            }
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    async def update_document(
        self,
        document_id: str,
        new_content: str,
        new_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a document in the vector database"""
        try:
            # Generate new embedding
            new_embedding = self.embedding_model.encode([new_content]).tolist()[0]
            
            # Update document
            self.collection.update(
                ids=[document_id],
                documents=[new_content],
                embeddings=[new_embedding],
                metadatas=[new_metadata]
            )
            
            logger.info(f"Updated document {document_id}")
            
            return {
                "updated_id": document_id,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        try:
            result = self.collection.get(ids=[document_id])
            
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None
    
    async def get_all_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all documents from the collection"""
        try:
            result = self.collection.get(limit=limit)
            
            documents = []
            for i in range(len(result["ids"])):
                documents.append({
                    "id": result["ids"][i],
                    "content": result["documents"][i],
                    "metadata": result["metadatas"][i]
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting all documents: {str(e)}")
            return []
    
    async def search_by_metadata(
        self,
        metadata_filter: Dict[str, Any],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents by metadata filters"""
        try:
            result = self.collection.get(
                where=metadata_filter,
                limit=k
            )
            
            documents = []
            for i in range(len(result["ids"])):
                documents.append({
                    "id": result["ids"][i],
                    "content": result["documents"][i],
                    "metadata": result["metadatas"][i]
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching by metadata: {str(e)}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            total_count = self.collection.count()
            
            # Get sample to analyze metadata
            sample = self.collection.get(limit=100)
            
            # Analyze languages
            languages = {}
            for metadata in sample["metadatas"]:
                lang = metadata.get("language", "unknown")
                languages[lang] = languages.get(lang, 0) + 1
            
            # Analyze chunk types
            chunk_types = {}
            for metadata in sample["metadatas"]:
                chunk_type = metadata.get("chunk_type", "unknown")
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            return {
                "total_documents": total_count,
                "collection_name": "code_chunks",
                "embedding_model": self.embedding_model_name,
                "languages": languages,
                "chunk_types": chunk_types,
                "database_path": self.db_path
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}
    
    async def clear_collection(self) -> Dict[str, Any]:
        """Clear all documents from the collection"""
        try:
            # Get current count
            old_count = self.collection.count()
            
            # Delete all documents
            self.collection.delete(where={})
            
            logger.info(f"Cleared {old_count} documents from collection")
            
            return {
                "cleared_count": old_count,
                "remaining_documents": 0
            }
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise
    
    async def backup_collection(self, backup_path: str) -> Dict[str, Any]:
        """Create a backup of the collection"""
        try:
            # Get all documents
            all_docs = await self.get_all_documents(limit=10000)
            
            # Save to file
            import json
            backup_file = Path(backup_path) / "vector_db_backup.json"
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_file, 'w') as f:
                json.dump(all_docs, f, indent=2)
            
            logger.info(f"Created backup with {len(all_docs)} documents at {backup_file}")
            
            return {
                "backup_path": str(backup_file),
                "documents_backed_up": len(all_docs),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise
    
    async def restore_collection(self, backup_path: str) -> Dict[str, Any]:
        """Restore collection from backup"""
        try:
            # Load backup
            import json
            backup_file = Path(backup_path) / "vector_db_backup.json"
            
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Clear current collection
            await self.clear_collection()
            
            # Restore documents
            documents = [doc["content"] for doc in backup_data]
            metadatas = [doc["metadata"] for doc in backup_data]
            ids = [doc["id"] for doc in backup_data]
            
            await self.add_documents(documents, metadatas, ids)
            
            logger.info(f"Restored {len(backup_data)} documents from backup")
            
            return {
                "backup_path": backup_path,
                "documents_restored": len(backup_data),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {str(e)}")
            raise
    
    async def optimize_collection(self) -> Dict[str, Any]:
        """Optimize the collection (compact and reorganize)"""
        try:
            # ChromaDB automatically handles optimization
            # This is a placeholder for any optimization operations
            
            stats = await self.get_collection_stats()
            
            logger.info("Collection optimization completed")
            
            return {
                "status": "optimized",
                "collection_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error optimizing collection: {str(e)}")
            raise
    
    async def close(self):
        """Close the vector database connection"""
        try:
            # ChromaDB handles connection cleanup automatically
            logger.info("Vector database connection closed")
        except Exception as e:
            logger.error(f"Error closing vector database: {str(e)}")