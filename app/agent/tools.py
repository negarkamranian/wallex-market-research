from abc import ABC, abstractmethod
from typing import Any, Dict
import random

from app.core.logging import get_logger

logger = get_logger(__name__)


class MarketTool(ABC):
    """Abstract base class for market research tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for the agent."""
        pass
    
    @abstractmethod
    def execute(self, asset: str) -> Dict[str, Any]:
        """Execute the tool.
        
        Args:
            asset: Asset symbol to analyze
            
        Returns:
            Tool execution result
        """
        pass


class GetMarketPriceTool(MarketTool):
    """Tool to retrieve current market price for an asset."""
    
    @property
    def name(self) -> str:
        return "get_market_price"
    
    @property
    def description(self) -> str:
        return (
            "Get the current market price for a cryptocurrency asset. "
            "Input should be the asset symbol (e.g., BTC, ETH). "
            "Returns price, 24h change, volume, and volatility metrics."
        )
    
    def execute(self, asset: str) -> Dict[str, Any]:
        """Get market price data (mocked).
        
        Args:
            asset: Asset symbol
            
        Returns:
            Market price data
        """
        logger.info(f"Executing get_market_price for {asset}")
        
        mock_prices = {
            "BTC": {"base": 45000, "volatility": "high"},
            "ETH": {"base": 2500, "volatility": "medium"},
            "USDT": {"base": 1, "volatility": "low"},
            "SOL": {"base": 100, "volatility": "high"},
        }
        
        base_data = mock_prices.get(asset.upper(), {"base": 1000, "volatility": "medium"})
        price = base_data["base"] + random.uniform(-base_data["base"] * 0.05, base_data["base"] * 0.05)
        change_24h = random.uniform(-15, 15)
        volume_24h = random.uniform(1000000, 50000000)
        
        result = {
            "asset": asset.upper(),
            "price_usd": round(price, 2),
            "change_24h_percent": round(change_24h, 2),
            "volume_24h_usd": round(volume_24h, 2),
            "volatility": base_data["volatility"]
        }
        
        logger.info(f"Market price result: {result}")
        return result


class GetInternalSentimentTool(MarketTool):
    """Tool to retrieve internal sentiment analysis for an asset."""
    
    @property
    def name(self) -> str:
        return "get_internal_sentiment"
    
    @property
    def description(self) -> str:
        return (
            "Get internal sentiment analysis and risk indicators for a cryptocurrency asset. "
            "Input should be the asset symbol (e.g., BTC, ETH). "
            "Returns sentiment score, risk indicators, and market outlook."
        )
    
    def execute(self, asset: str) -> Dict[str, Any]:
        """Get internal sentiment data (mocked).
        
        Args:
            asset: Asset symbol
            
        Returns:
            Sentiment analysis data
        """
        logger.info(f"Executing get_internal_sentiment for {asset}")
        
        sentiment_score = random.uniform(0.3, 0.9)
        
        if sentiment_score < 0.4:
            risk_level = "High"
            outlook = "bearish"
        elif sentiment_score < 0.6:
            risk_level = "Medium"
            outlook = "neutral"
        else:
            risk_level = "Low"
            outlook = "bullish"
        
        social_sentiment = random.uniform(0.4, 0.95)
        news_sentiment = random.uniform(0.3, 0.9)
        
        result = {
            "asset": asset.upper(),
            "sentiment_score": round(sentiment_score, 2),
            "risk_level": risk_level,
            "social_sentiment": round(social_sentiment, 2),
            "news_sentiment": round(news_sentiment, 2),
            "market_outlook": outlook,
            "confidence": round(random.uniform(0.7, 0.95), 2)
        }
        
        logger.info(f"Sentiment result: {result}")
        return result


AVAILABLE_TOOLS = [
    GetMarketPriceTool(),
    GetInternalSentimentTool(),
]

