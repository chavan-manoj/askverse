from typing import List, Dict, Any
import asyncio
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

from ..core.config import settings
from ..services.confluence import ConfluenceService
from ..services.vector_store import VectorStoreService
from ..db.models import Document, DocumentSync
from ..db.session import get_db

logger = logging.getLogger(__name__)

class DocumentSyncService:
    def __init__(self):
        self.confluence = ConfluenceService()
        self.vector_store = VectorStoreService()
        self.db = next(get_db())
    
    async def process_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document and generate embeddings."""
        try:
            # Extract content and metadata
            content = doc.get("content", "")
            title = doc.get("title", "")
            url = doc.get("url", "")
            doc_id = doc.get("id", "")
            
            # Generate embeddings
            embeddings = await self.vector_store.generate_embeddings(content)
            
            # Create document record
            document = Document(
                id=doc_id,
                title=title,
                content=content,
                url=url,
                embeddings=embeddings,
                source_type="confluence",
                last_updated=datetime.utcnow()
            )
            
            # Store in vector database
            await self.vector_store.store_document(document)
            
            # Store in relational database
            self.db.add(document)
            self.db.commit()
            
            return {
                "id": doc_id,
                "title": title,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error processing document {doc.get('id')}: {str(e)}")
            return {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "status": "error",
                "error": str(e)
            }
    
    async def sync_documents(self) -> Dict[str, Any]:
        """Synchronize documents from Confluence to vector database."""
        try:
            # Create sync record
            sync = DocumentSync(
                start_time=datetime.utcnow(),
                status="running"
            )
            self.db.add(sync)
            self.db.commit()
            
            # Fetch documents from Confluence
            documents = await self.confluence.fetch_documents()
            
            # Process documents
            tasks = [self.process_document(doc) for doc in documents]
            results = await asyncio.gather(*tasks)
            
            # Update sync record
            sync.end_time = datetime.utcnow()
            sync.status = "completed"
            sync.total_documents = len(documents)
            sync.successful_documents = len([r for r in results if r["status"] == "success"])
            sync.failed_documents = len([r for r in results if r["status"] == "error"])
            sync.error_log = json.dumps([r for r in results if r["status"] == "error"])
            
            self.db.commit()
            
            return {
                "status": "success",
                "total_documents": sync.total_documents,
                "successful_documents": sync.successful_documents,
                "failed_documents": sync.failed_documents
            }
            
        except Exception as e:
            logger.error(f"Error in document sync: {str(e)}")
            
            # Update sync record with error
            sync.end_time = datetime.utcnow()
            sync.status = "failed"
            sync.error_log = str(e)
            self.db.commit()
            
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup_old_documents(self, days: int = 30) -> Dict[str, Any]:
        """Remove documents older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get old documents
            old_docs = self.db.query(Document).filter(
                Document.last_updated < cutoff_date
            ).all()
            
            # Remove from vector database
            for doc in old_docs:
                await self.vector_store.delete_document(doc.id)
            
            # Remove from relational database
            for doc in old_docs:
                self.db.delete(doc)
            self.db.commit()
            
            return {
                "status": "success",
                "removed_documents": len(old_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in document cleanup: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            } 