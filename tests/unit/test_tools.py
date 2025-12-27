import pytest
from app.agent.tools import GetMarketPriceTool, GetInternalSentimentTool


class TestGetMarketPriceTool:

    def test_name_property(self):
        tool = GetMarketPriceTool()
        assert tool.name == "get_market_price"

    def test_description_property(self):
        tool = GetMarketPriceTool()
        assert "current market price" in tool.description.lower()
        assert "cryptocurrency asset" in tool.description.lower()

    def test_execute_known_asset(self):
        tool = GetMarketPriceTool()
        result = tool.execute("BTC")

        assert result["asset"] == "BTC"
        assert isinstance(result["price_usd"], float)
        assert isinstance(result["change_24h_percent"], float)
        assert isinstance(result["volume_24h_usd"], float)
        assert result["volatility"] in ["low", "medium", "high"]

    def test_execute_unknown_asset(self):
        tool = GetMarketPriceTool()
        result = tool.execute("UNKNOWN")

        assert result["asset"] == "UNKNOWN"
        assert isinstance(result["price_usd"], float)
        assert result["volatility"] == "medium"

    def test_execute_case_insensitive(self):
        tool = GetMarketPriceTool()
        result = tool.execute("eth")

        assert result["asset"] == "ETH"


class TestGetInternalSentimentTool:

    def test_name_property(self):
        tool = GetInternalSentimentTool()
        assert tool.name == "get_internal_sentiment"

    def test_description_property(self):
        tool = GetInternalSentimentTool()
        assert "internal sentiment analysis" in tool.description.lower()
        assert "risk indicators" in tool.description.lower()

    def test_execute_returns_expected_keys(self):
        tool = GetInternalSentimentTool()
        result = tool.execute("BTC")

        expected_keys = [
            "asset", "sentiment_score", "risk_level",
            "social_sentiment", "news_sentiment", "market_outlook", "confidence"
        ]

        for key in expected_keys:
            assert key in result

    def test_execute_sentiment_score_range(self):
        tool = GetInternalSentimentTool()
        result = tool.execute("BTC")

        assert 0.3 <= result["sentiment_score"] <= 0.9

    def test_execute_risk_level_based_on_sentiment(self):
        tool = GetInternalSentimentTool()

        import random
        original_uniform = random.uniform

        random.uniform = lambda a, b: min(a, b) if a == 0.3 else original_uniform(a, b)
        result = tool.execute("BTC")
        assert result["risk_level"] == "High"
        assert result["market_outlook"] == "bearish"

        random.uniform = original_uniform

    def test_execute_case_insensitive(self):
        tool = GetInternalSentimentTool()
        result = tool.execute("btc")

        assert result["asset"] == "BTC"