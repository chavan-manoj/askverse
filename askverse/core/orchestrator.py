from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from ..agents.document import DocumentAgent
from ..agents.api import APIAgent
from ..agents.data import DataAgent
from ..agents.base import AgentResponse

class QueryOrchestrator:
    def __init__(self):
        self.document_agent = DocumentAgent()
        self.api_agent = APIAgent()
        self.data_agent = DataAgent()
        
        # Create orchestration prompt
        self.orchestrate_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a query orchestrator that decomposes complex queries into sub-tasks."),
            ("user", "Decompose this query into sub-tasks and determine which agents should handle them:"
                   "\n\nQuery: {query}"
                   "\n\nContext: {context}"
                   "\n\nReturn a JSON object with the following structure:"
                   "\n{"
                   "\n  'sub_tasks': ["
                   "\n    {"
                   "\n      'task': 'description of the task',"
                   "\n      'agent': 'document|api|data',"
                   "\n      'priority': 1-3"
                   "\n    }"
                   "\n  ]"
                   "\n}")
        ])
        
        self.llm = self.document_agent.llm  # Reuse the same LLM instance
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query by orchestrating multiple agents."""
        try:
            # Decompose query into sub-tasks
            orchestrate_chain = LLMChain(llm=self.llm, prompt=self.orchestrate_prompt)
            decomposition = orchestrate_chain.invoke({
                "query": query,
                "context": context or {}
            })
            
            # Parse sub-tasks
            sub_tasks = decomposition["text"]
            
            # Sort tasks by priority
            sub_tasks.sort(key=lambda x: x["priority"])
            
            # Process tasks with each agent
            results = []
            for task in sub_tasks:
                agent = self._get_agent(task["agent"])
                if agent:
                    response = await agent.process(query, context)
                    if response.success:
                        results.append({
                            "task": task["task"],
                            "agent": task["agent"],
                            "response": response.data,
                            "confidence": response.confidence
                        })
            
            # Aggregate results
            final_response = await self.data_agent.process(
                query,
                {
                    "data_sources": results,
                    "original_query": query,
                    "context": context or {}
                }
            )
            
            return {
                "success": True,
                "response": final_response.data["response"],
                "confidence": final_response.confidence,
                "sub_tasks": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None,
                "confidence": 0.0,
                "sub_tasks": []
            }
    
    def _get_agent(self, agent_type: str) -> Any:
        """Get the appropriate agent based on type."""
        agents = {
            "document": self.document_agent,
            "api": self.api_agent,
            "data": self.data_agent
        }
        return agents.get(agent_type) 