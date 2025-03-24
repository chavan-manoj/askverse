from typing import List, Dict, Any
import pinecone
from sentence_transformers import SentenceTransformer
import numpy as np

from ..config.settings import settings

class VectorStore:
    def __init__(self):
        # Initialize Pinecone
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        
        # Get or create index
        if settings.PINECONE_INDEX not in pinecone.list_indexes():
            pinecone.create_index(
                name=settings.PINECONE_INDEX,
                dimension=768,  # Default dimension for sentence-transformers
                metric="cosine"
            )
        
        self.index = pinecone.Index(settings.PINECONE_INDEX)
        
        # Initialize sentence transformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Upsert documents to the vector store."""
        vectors = []
        for doc in documents:
            # Generate embedding
            embedding = self.model.encode(doc["content"]).tolist()
            
            # Prepare metadata
            metadata = {
                "content": doc["content"],
                "source_type": doc["source_type"],
                "source_id": doc["source_id"],
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "last_updated": doc.get("last_updated", "")
            }
            
            vectors.append({
                "id": doc["id"],
                "values": embedding,
                "metadata": metadata
            })
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Search in Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            })
        
        return formatted_results
    
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the vector store."""
        self.index.delete(ids=document_ids)
    
    def update_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Update a document in the vector store."""
        # Generate new embedding
        embedding = self.model.encode(content).tolist()
        
        # Update in Pinecone
        self.index.upsert(vectors=[{
            "id": document_id,
            "values": embedding,
            "metadata": metadata
        }]) 