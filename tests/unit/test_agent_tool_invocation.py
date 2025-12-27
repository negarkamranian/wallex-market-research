import pytest
from unittest.mock import MagicMock, patch
from app.agent.market_agent import MarketResearchAgent
from app.agent.tools import GetMarketPriceTool, GetInternalSentimentTool


class TestAgentToolInvocation:

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_agent_calls_market_price_tool(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()
        action_mock = MagicMock()
        action_mock.tool = "get_market_price"
        action_mock.tool_input = "BTC"
        action_mock.log = "Using get_market_price tool"

        observation = '{"price_usd": 45000, "change_24h_percent": 2.5, "volume_24h_usd": 25000000, "volatility": "high"}'

        mock_executor.invoke.return_value = {
            "output": '{"asset": "BTC", "risk_level": "Low", "sentiment_score": 0.8, "tools_used": ["get_market_price"]}',
            "intermediate_steps": [(action_mock, observation)]
        }
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            result = agent.research("BTC")

        assert len(result["tool_calls"]) == 1
        tool_call = result["tool_calls"][0]
        assert tool_call["tool"] == "get_market_price"
        assert tool_call["input"] == "BTC"
        assert tool_call["output"] == observation

        assert len(result["agent_steps"]) == 1
        step = result["agent_steps"][0]
        assert step["action"] == "get_market_price"
        assert step["thought"] == "Using get_market_price tool"

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_agent_calls_multiple_tools(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()

        actions = []
        observations = []

        action1 = MagicMock()
        action1.tool = "get_market_price"
        action1.tool_input = "BTC"
        action1.log = "Getting market price"
        actions.append(action1)
        observations.append('{"price_usd": 45000}')

        action2 = MagicMock()
        action2.tool = "get_internal_sentiment"
        action2.tool_input = "BTC"
        action2.log = "Getting sentiment analysis"
        actions.append(action2)
        observations.append('{"sentiment_score": 0.7}')

        mock_executor.invoke.return_value = {
            "output": '{"asset": "BTC", "risk_level": "Medium", "sentiment_score": 0.7, "tools_used": ["get_market_price", "get_internal_sentiment"]}',
            "intermediate_steps": list(zip(actions, observations))
        }
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            result = agent.research("BTC")

        assert len(result["tool_calls"]) == 2
        assert result["tool_calls"][0]["tool"] == "get_market_price"
        assert result["tool_calls"][1]["tool"] == "get_internal_sentiment"

        assert len(result["agent_steps"]) == 2

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_agent_no_tools_used(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {
            "output": '{"asset": "BTC", "risk_level": "Low", "sentiment_score": 0.9, "tools_used": []}',
            "intermediate_steps": []
        }
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            result = agent.research("BTC")

        assert len(result["tool_calls"]) == 0
        assert len(result["agent_steps"]) == 0
        assert result["output"]["tools_used"] == []

    @patch('app.agent.market_agent.ChatOpenAI')
    @patch('app.agent.market_agent.create_openai_functions_agent')
    @patch('app.agent.market_agent.AgentExecutor')
    def test_agent_tools_used_in_output_matches_calls(self, mock_agent_executor, mock_create_agent, mock_llm_class, mock_settings):
        mock_executor = MagicMock()

        action = MagicMock()
        action.tool = "get_internal_sentiment"
        action.tool_input = "ETH"

        mock_executor.invoke.return_value = {
            "output": '{"asset": "ETH", "risk_level": "Medium", "sentiment_score": 0.6, "tools_used": ["get_internal_sentiment"]}',
            "intermediate_steps": [(action, '{"sentiment_score": 0.6}')]
        }
        mock_agent_executor.return_value = mock_executor

        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            result = agent.research("ETH")

        assert result["output"]["tools_used"] == ["get_internal_sentiment"]
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool"] == "get_internal_sentiment"

    def test_langchain_tools_creation(self, mock_settings):
        with patch('app.agent.market_agent.settings', mock_settings):
            agent = MarketResearchAgent()
            tools = agent._create_langchain_tools()

        assert len(tools) == 2

        tool_names = [tool.name for tool in tools]
        assert "get_market_price" in tool_names
        assert "get_internal_sentiment" in tool_names

        market_tool = next(t for t in tools if t.name == "get_market_price")
        result = market_tool.func("BTC")
        assert isinstance(result, str)
        assert '"asset": "BTC"' in result