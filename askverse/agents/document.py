from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from .base import BaseAgent, AgentResponse
from ..services.vector_store import VectorStore
from ..services.confluence import ConfluenceService

class DocumentAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.vector_store = VectorStore()
        self.confluence = ConfluenceService()
        
        # Create specialized prompts
        self.search_prompt = self._create_prompt(
            "Based on the following query and context, identify the most relevant documents:"
            "\n\nQuery: {query}"
            "\n\nContext: {context}"
            "\n\nRelevant documents: {documents}"
            "\n\nProvide a comprehensive answer based on the documents."
        )
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Process the query and search for relevant documents."""
        try:
            # Search in vector store
            vector_results = self.vector_store.search(query, top_k=5)
            
            # Search in Confluence
            confluence_results = await self.confluence.search_pages(query)
            
            # Combine results
            all_documents = []
            
            # Process vector store results
            for result in vector_results:
                doc = {
                    "source": "vector_store",
                    "content": result["metadata"]["content"],
                    "title": result["metadata"].get("title", ""),
                    "url": result["metadata"].get("url", ""),
                    "relevance_score": result["score"]
                }
                all_documents.append(doc)
            
            # Process Confluence results
            for result in confluence_results:
                doc = {
                    "source": "confluence",
                    "content": result["content"],
                    "title": result["title"],
                    "url": result["url"],
                    "relevance_score": 1.0  # Default score for Confluence results
                }
                all_documents.append(doc)
            
            # Sort by relevance score
            all_documents.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Generate response using LLM
            search_chain = LLMChain(llm=self.llm, prompt=self.search_prompt)
            response = search_chain.invoke({
                "query": query,
                "context": context or {},
                "documents": all_documents
            })
            
            # Calculate confidence
            confidence = self._calculate_confidence(response["text"], context or {})
            
            # Mask PII
            masked_response = self._mask_pii(response["text"])
            
            return AgentResponse(
                success=True,
                data={
                    "response": masked_response,
                    "documents": all_documents,
                    "confidence": confidence
                },
                confidence=confidence
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                data={},
                confidence=0.0,
                error=str(e)
            ) 