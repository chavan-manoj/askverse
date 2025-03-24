from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base

class APIKey(Base):
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, unique=True, index=True)
    client_secret = Column(String)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    
    # Relationships
    user = relationship("User", back_populates="api_keys") 