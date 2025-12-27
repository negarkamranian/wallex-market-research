import os
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


os.environ['OPENROUTER_API_KEY'] = 'test_key'
os.environ['LLM_MODEL'] = 'test_model'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'test_db'
os.environ['POSTGRES_USER'] = 'test_user'
os.environ['POSTGRES_PASSWORD'] = 'test_pass'
os.environ['MONGO_HOST'] = 'localhost'
os.environ['MONGO_PORT'] = '27017'
os.environ['MONGO_DB'] = 'test_mongo'

from app.db.models import Base


@pytest.fixture
def mock_settings():
    from app.core.config import Settings
    return Settings(
        openrouter_api_key="test_key",
        llm_model="test_model",
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="test_db",
        postgres_user="test_user",
        postgres_password="test_pass",
        mongo_host="localhost",
        mongo_port=27017,
        mongo_db="test_mongo",
    )





@pytest.fixture
def mock_llm():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = {
        "output": '{"asset": "BTC", "risk_level": "Low", "sentiment_score": 0.8, "tools_used": ["get_market_price"], "analysis": "Test analysis"}',
        "intermediate_steps": [
            (MagicMock(tool="get_market_price", tool_input="BTC", log=""), '{"price_usd": 45000}')
        ]
    }
    return mock_llm


@pytest.fixture
def mock_agent_executor(mock_llm):
    mock_executor = MagicMock()
    mock_executor.invoke.return_value = {
        "output": '{"asset": "BTC", "risk_level": "Low", "sentiment_score": 0.8, "tools_used": ["get_market_price"], "analysis": "Test analysis"}',
        "intermediate_steps": [
            (MagicMock(tool="get_market_price", tool_input="BTC", log=""), '{"price_usd": 45000}')
        ]
    }
    return mock_executor


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def mock_postgres_client(in_memory_db):
    mock_client = MagicMock()
    mock_client.get_session.return_value = in_memory_db
    return mock_client


@pytest.fixture
def research_repository(mock_postgres_client):
    return ResearchRepository(mock_postgres_client)


@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine("postgresql://test_user:test_pass@localhost:5432/test_db")
    yield engine
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    Base.metadata.create_all(bind=test_db_engine)

    yield session

    session.rollback()
    session.close()