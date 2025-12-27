from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import Base, ResearchRequest, ResearchReport

logger = get_logger(__name__)


class PostgresClient:
    """PostgreSQL database client with connection pooling."""
    
    def __init__(self):
        """Initialize PostgreSQL client."""
        self.engine = create_engine(
            settings.postgres_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
    def init_db(self) -> None:
        """Initialize database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()


class ResearchRepository:
    """Repository for research data operations."""
    
    def __init__(self, db_client: PostgresClient):
        """Initialize repository.
        
        Args:
            db_client: PostgreSQL client instance
        """
        self.db_client = db_client
    
    def create_request(self, asset: str) -> ResearchRequest:
        """
        Args:
            asset: Asset symbol
            
        Returns:
            Created research request
        """
        session = self.db_client.get_session()
        try:
            request = ResearchRequest(asset=asset)
            session.add(request)
            session.commit()
            session.refresh(request)
            logger.info(f"Created research request for asset: {asset}, id: {request.id}")
            return request
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create research request: {e}")
            raise
        finally:
            session.close()
    
    def create_report(
        self,
        request_id: int,
        asset: str,
        risk_level: str,
        sentiment_score: float,
        tools_used: list[str],
        report_data: dict
    ) -> ResearchReport:
        """
        Args:
            request_id: ID of the research request
            asset: Asset symbol
            risk_level: Risk level assessment
            sentiment_score: Sentiment score value
            tools_used: List of tools used by the agent
            report_data: Full report data as JSON
            
        Returns:
            Created research report
        """
        session = self.db_client.get_session()
        try:
            report = ResearchReport(
                request_id=request_id,
                asset=asset,
                risk_level=risk_level,
                sentiment_score=str(sentiment_score),
                tools_used=tools_used,
                report_data=report_data
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            logger.info(f"Created research report for request_id: {request_id}")
            return report
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create research report: {e}")
            raise
        finally:
            session.close()
    
    def get_report_by_request_id(self, request_id: int) -> Optional[ResearchReport]:
        """
        Args:
            request_id: ID of the research request
            
        Returns:
            Research report if found, None otherwise
        """
        session = self.db_client.get_session()
        try:
            report = session.query(ResearchReport).filter(
                ResearchReport.request_id == request_id
            ).first()
            return report
        finally:
            session.close()


postgres_client = PostgresClient()
research_repository = ResearchRepository(postgres_client)
