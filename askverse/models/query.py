from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base

class Query(Base):
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String)
    response_text = Column(String)
    confidence_score = Column(Float)
    processing_time = Column(Float)  # in seconds
    user_id = Column(Integer, ForeignKey("user.id"))
    metadata = Column(JSON)  # Store additional query metadata
    
    # Relationships
    user = relationship("User", back_populates="queries")
    sources = relationship("QuerySource", back_populates="query")

class QuerySource(Base):
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("query.id"))
    source_type = Column(String)  # e.g., "confluence", "api", "vector_db"
    source_id = Column(String)  # e.g., confluence page ID, API endpoint
    relevance_score = Column(Float)
    content = Column(String)
    
    # Relationships
    query = relationship("Query", back_populates="sources") 