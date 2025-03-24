from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from ..config.settings import settings

class AgentResponse(BaseModel):
    """Base response model for all agents."""
    success: bool
    data: Dict[str, Any]
    confidence: float
    error: str = ""

class BaseAgent(ABC):
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        )
        self.output_parser = PydanticOutputParser(pydantic_object=AgentResponse)
    
    @abstractmethod
    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Process the query and return a response."""
        pass
    
    def _create_prompt(self, template: str) -> ChatPromptTemplate:
        """Create a chat prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant."),
            ("user", template)
        ])
    
    def _calculate_confidence(self, response: str, context: Dict[str, Any]) -> float:
        """Calculate confidence score for the response."""
        # This is a simple implementation - can be enhanced with more sophisticated methods
        confidence_prompt = self._create_prompt(
            "Rate the confidence of this response on a scale of 0 to 1: {response}"
        )
        
        confidence_chain = confidence_prompt | self.llm
        confidence_response = confidence_chain.invoke({"response": response})
        
        try:
            # Extract numeric value from response
            confidence = float(confidence_response.content.strip())
            return max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
        except ValueError:
            return 0.5  # Default confidence if parsing fails
    
    def _mask_pii(self, text: str) -> str:
        """Mask Personally Identifiable Information in the text."""
        pii_prompt = self._create_prompt(
            "Mask any Personally Identifiable Information (PII) in this text: {text}"
        )
        
        pii_chain = pii_prompt | self.llm
        masked_text = pii_chain.invoke({"text": text})
        
        return masked_text.content.strip() 