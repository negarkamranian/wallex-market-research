from pydantic import BaseModel, Field
from typing import List


class ResearchRequest(BaseModel):
    """Request model for market research endpoint."""
    
    asset: str = Field(..., description="Asset symbol (e.g., BTC, ETH)", min_length=1, max_length=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "asset": "BTC"
            }
        }


class ResearchResponse(BaseModel):
    """Response model for market research endpoint."""
    
    asset: str = Field(..., description="Asset symbol")
    risk_level: str = Field(..., description="Risk level: Low, Medium, or High")
    sentiment_score: float = Field(..., description="Sentiment score between 0 and 1")
    tools_used: List[str] = Field(..., description="List of tools used by the agent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "asset": "BTC",
                "risk_level": "High",
                "sentiment_score": 0.72,
                "tools_used": ["get_market_price", "get_internal_sentiment"]
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: str = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Research failed",
                "detail": "Failed to generate valid output after 3 attempts"
            }
        }
