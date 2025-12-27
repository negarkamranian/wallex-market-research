import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
from app.agent.market_agent import MarketResearchAgent, MarketResearchOutput


class TestMarketResearchOutput:

    def test_valid_output(self):
        output = MarketResearchOutput(
            asset="BTC",
            risk_level="Low",
            sentiment_score=0.8,
            tools_used=["get_market_price"],
            analysis="Test analysis"
        )
        assert output.asset == "BTC"
        assert output.risk_level == "Low"

    def test_invalid_risk_level(self):
        with pytest.raises(ValueError):
            output = MarketResearchOutput(
                asset="BTC",
                risk_level="Invalid",
                sentiment_score=0.8,
                tools_used=["get_market_price"]
            )
            output.validate_risk_level()

    def test_validate_risk_level(self):
        output = MarketResearchOutput(
            asset="BTC",
            risk_level="Medium",
            sentiment_score=0.8,
            tools_used=["get_market_price"]
        )
        result = output.validate_risk_level()
        assert result is output


class TestMarketResearchAgent:

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_initialization(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        mock_executor = MagicMock()
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()

        assert agent.llm == mock_llm
        assert agent.tools is not None
        assert agent.agent_executor == mock_executor

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_research_success(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {
            "output": '{"asset": "BTC", "risk_level": "Low", "sentiment_score": 0.8, "tools_used": ["get_market_price"], "analysis": "Test analysis"}',
            "intermediate_steps": [
                (MagicMock(tool="get_market_price", tool_input="BTC", log=""), '{"price_usd": 45000}')
            ]
        }
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            result = agent.research("BTC")

        assert result["success"] is True
        assert result["output"]["asset"] == "BTC"
        assert result["output"]["risk_level"] == "Low"
        assert result["output"]["sentiment_score"] == 0.8
        assert "execution_time_ms" in result

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_research_json_parsing_with_extra_text(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {
            "output": 'Some extra text {"asset": "BTC", "risk_level": "Medium", "sentiment_score": 0.6, "tools_used": ["get_market_price"]} more text',
            "intermediate_steps": []
        }
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            result = agent.research("BTC")

        assert result["output"]["asset"] == "BTC"
        assert result["output"]["risk_level"] == "Medium"

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_research_validation_error_retry(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()
        mock_executor.invoke.side_effect = [
            {"output": "invalid json", "intermediate_steps": []},
            {"output": '{"asset": "BTC", "risk_level": "Low", "sentiment_score": 0.8, "tools_used": ["get_market_price"]}', "intermediate_steps": []}
        ]
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            result = agent.research("BTC", max_retries=2)

        assert result["success"] is True
        assert mock_executor.invoke.call_count == 2

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_research_max_retries_exceeded(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": "invalid json", "intermediate_steps": []}
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()

        with pytest.raises(Exception) as exc_info:
            agent.research("BTC", max_retries=1)

        assert "Failed to generate valid output" in str(exc_info.value)

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_research_asset_correction(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {
            "output": '{"asset": "btc", "risk_level": "Low", "sentiment_score": 0.8, "tools_used": ["get_market_price"]}',
            "intermediate_steps": []
        }
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            result = agent.research("BTC")

        assert result["output"]["asset"] == "BTC"

    def test_parse_and_validate_output_valid(self):
        with patch('app.agent.market_agent.settings'):
            agent = MarketResearchAgent()
            output_text = '{"asset": "BTC", "risk_level": "High", "sentiment_score": 0.3, "tools_used": ["get_market_price"], "analysis": "Test"}'
            result = agent._parse_and_validate_output(output_text, "BTC")

        assert result["asset"] == "BTC"
        assert result["risk_level"] == "High"

    def test_parse_and_validate_output_invalid_json(self):
        with patch('app.agent.market_agent.settings'):
            agent = MarketResearchAgent()

        with pytest.raises(ValueError):
            agent._parse_and_validate_output("not json", "BTC")

    def test_parse_and_validate_output_invalid_risk_level(self):
        with patch('app.agent.market_agent.settings'):
            agent = MarketResearchAgent()
            output_text = '{"asset": "BTC", "risk_level": "Invalid", "sentiment_score": 0.5, "tools_used": []}'

        with pytest.raises(ValidationError):
            agent._parse_and_validate_output(output_text, "BTC")