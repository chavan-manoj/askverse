from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from .base import BaseAgent, AgentResponse

class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
        # Create specialized prompts
        self.transform_prompt = self._create_prompt(
            "Transform and clean the following data according to the specified requirements:"
            "\n\nData: {data}"
            "\n\nRequirements: {requirements}"
            "\n\nReturn the transformed data in a structured format."
        )
        
        self.aggregate_prompt = self._create_prompt(
            "Aggregate and combine the following data sources into a coherent response:"
            "\n\nData sources: {sources}"
            "\n\nQuery: {query}"
            "\n\nContext: {context}"
            "\n\nProvide a comprehensive answer that combines all relevant information."
        )
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Process and transform data from various sources."""
        try:
            # Get data sources from context
            data_sources = context.get("data_sources", [])
            
            if not data_sources:
                return AgentResponse(
                    success=True,
                    data={"response": "No data sources provided for processing."},
                    confidence=1.0
                )
            
            # Process each data source
            processed_sources = []
            for source in data_sources:
                # Transform data if needed
                if source.get("needs_transform", False):
                    transform_chain = LLMChain(llm=self.llm, prompt=self.transform_prompt)
                    transformed_data = transform_chain.invoke({
                        "data": source["data"],
                        "requirements": source.get("requirements", {})
                    })
                    source["data"] = transformed_data["text"]
                
                processed_sources.append(source)
            
            # Aggregate results
            aggregate_chain = LLMChain(llm=self.llm, prompt=self.aggregate_prompt)
            response = aggregate_chain.invoke({
                "sources": processed_sources,
                "query": query,
                "context": context or {}
            })
            
            # Calculate confidence
            confidence = self._calculate_confidence(response["text"], context or {})
            
            # Mask PII
            masked_response = self._mask_pii(response["text"])
            
            return AgentResponse(
                success=True,
                data={
                    "response": masked_response,
                    "processed_sources": processed_sources,
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
    
    def transform_data(self, data: Any, requirements: Dict[str, Any]) -> Any:
        """Transform data according to specific requirements."""
        transform_chain = LLMChain(llm=self.llm, prompt=self.transform_prompt)
        response = transform_chain.invoke({
            "data": data,
            "requirements": requirements
        })
        return response["text"]
    
    def aggregate_data(self, sources: List[Dict[str, Any]], query: str, context: Dict[str, Any] = None) -> str:
        """Aggregate data from multiple sources."""
        aggregate_chain = LLMChain(llm=self.llm, prompt=self.aggregate_prompt)
        response = aggregate_chain.invoke({
            "sources": sources,
            "query": query,
            "context": context or {}
        })
        return response["text"] 