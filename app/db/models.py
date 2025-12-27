from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ResearchRequest(Base):
    """Model for storing incoming research requests."""
    
    __tablename__ = "research_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ResearchRequest(id={self.id}, asset={self.asset})>"


class ResearchReport(Base):
    """Model for storing final validated research reports."""
    
    __tablename__ = "research_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)
    risk_level = Column(String(20), nullable=False)
    sentiment_score = Column(String(10), nullable=False)
    tools_used = Column(JSON, nullable=False)
    report_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ResearchReport(id={self.id}, asset={self.asset}, risk_level={self.risk_level})>"
