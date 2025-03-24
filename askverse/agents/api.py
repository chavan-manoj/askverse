from typing import Dict, Any, List
import httpx
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from .base import BaseAgent, AgentResponse
from ..services.openapi import OpenAPIService
from ..config.settings import settings

class APIAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.openapi_service = OpenAPIService()
        self.client = httpx.Client(timeout=30.0)
        
        # Create specialized prompts
        self.api_prompt = self._create_prompt(
            "Based on the following query and available API endpoints, identify and call the most relevant APIs:"
            "\n\nQuery: {query}"
            "\n\nContext: {context}"
            "\n\nAvailable endpoints: {endpoints}"
            "\n\nProvide a comprehensive answer based on the API responses."
        )
        
        self.param_prompt = self._create_prompt(
            "Extract the necessary parameters for this API call from the query:"
            "\n\nQuery: {query}"
            "\n\nEndpoint: {endpoint}"
            "\n\nRequired parameters: {parameters}"
            "\n\nReturn a JSON object with the extracted parameters."
        )
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Process the query and interact with relevant APIs."""
        try:
            # Search for relevant endpoints
            endpoints = self.openapi_service.search_endpoints(query)
            
            if not endpoints:
                return AgentResponse(
                    success=True,
                    data={"response": "No relevant APIs found for this query."},
                    confidence=1.0
                )
            
            # Process each endpoint
            api_responses = []
            for endpoint_info in endpoints:
                endpoint = endpoint_info["endpoint"]
                
                # Extract parameters
                param_chain = LLMChain(llm=self.llm, prompt=self.param_prompt)
                params = param_chain.invoke({
                    "query": query,
                    "endpoint": endpoint,
                    "parameters": endpoint.get("parameters", [])
                })
                
                try:
                    # Make API call
                    response = self._make_api_call(
                        endpoint["url"],
                        endpoint["method"],
                        params
                    )
                    
                    api_responses.append({
                        "endpoint": endpoint,
                        "response": response
                    })
                except Exception as e:
                    print(f"Error calling API {endpoint['url']}: {e}")
                    continue
            
            if not api_responses:
                return AgentResponse(
                    success=True,
                    data={"response": "Unable to get responses from any APIs."},
                    confidence=0.5
                )
            
            # Generate response using LLM
            api_chain = LLMChain(llm=self.llm, prompt=self.api_prompt)
            response = api_chain.invoke({
                "query": query,
                "context": context or {},
                "endpoints": api_responses
            })
            
            # Calculate confidence
            confidence = self._calculate_confidence(response["text"], context or {})
            
            # Mask PII
            masked_response = self._mask_pii(response["text"])
            
            return AgentResponse(
                success=True,
                data={
                    "response": masked_response,
                    "api_responses": api_responses,
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
    
    def _make_api_call(self, url: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make an API call with the given parameters."""
        headers = {}
        
        # Add API keys if needed
        if "weather" in url and settings.WEATHER_API_KEY:
            headers["Authorization"] = f"Bearer {settings.WEATHER_API_KEY}"
        elif "maps" in url and settings.MAPS_API_KEY:
            headers["Authorization"] = f"Bearer {settings.MAPS_API_KEY}"
        
        # Make request
        response = self.client.request(
            method=method,
            url=url,
            params=params,
            headers=headers
        )
        response.raise_for_status()
        
        return response.json() 