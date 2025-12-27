from datetime import datetime
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoDBClient:
    """MongoDB client for storing AI execution logs."""
    
    def __init__(self):
        """Initialize MongoDB client."""
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(
                settings.mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[settings.mongo_db]
            self.collection = self.db['ai_execution_logs']
            logger.info("MongoDB connection established successfully")
        except ConnectionFailure as e:
            logger.warning(f"MongoDB connection failed: {e}. Logs will be skipped.")
            self.client = None
        except Exception as e:
            logger.warning(f"MongoDB initialization failed: {e}. Logs will be skipped.")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if MongoDB is available.
        
        Returns:
            True if MongoDB is connected, False otherwise
        """
        if not self.client:
            return False
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def log_execution(
        self,
        request_id: int,
        asset: str,
        agent_steps: list[Dict[str, Any]],
        tool_calls: list[Dict[str, Any]],
        final_output: Dict[str, Any],
        execution_time_ms: float,
        success: bool,
        error: Optional[str] = None
    ) -> Optional[str]:
        """
        Args:
            request_id: ID of the research request
            asset: Asset symbol
            agent_steps: List of agent reasoning steps
            tool_calls: List of tool invocations
            final_output: Final structured output
            execution_time_ms: Execution time in milliseconds
            success: Whether execution was successful
            error: Error message if execution failed
            
        Returns:
            MongoDB document ID if successful, None otherwise
        """
        if not self.is_available():
            logger.warning("MongoDB not available, skipping execution log")
            return None
        
        try:
            document = {
                "request_id": request_id,
                "asset": asset,
                "agent_steps": agent_steps,
                "tool_calls": tool_calls,
                "final_output": final_output,
                "execution_time_ms": execution_time_ms,
                "success": success,
                "error": error,
                "timestamp": datetime.utcnow()
            }
            
            result = self.collection.insert_one(document)
            logger.info(f"AI execution logged to MongoDB: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.warning(f"Failed to log to MongoDB: {e}. Continuing without logging.")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error logging to MongoDB: {e}. Continuing without logging.")
            return None
    
    def get_execution_log(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Args:
            request_id: ID of the research request
            
        Returns:
            Execution log document if found, None otherwise
        """
        if not self.is_available():
            return None
        
        try:
            document = self.collection.find_one({"request_id": request_id})
            if document:
                document['_id'] = str(document['_id'])
            return document
        except Exception as e:
            logger.warning(f"Failed to retrieve execution log: {e}")
            return None
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


mongodb_client = MongoDBClient()
