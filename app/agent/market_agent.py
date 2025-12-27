import json
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings
from app.core.logging import get_logger
from app.agent.tools import AVAILABLE_TOOLS
from app.agent.prompts import SYSTEM_PROMPT, get_research_prompt

logger = get_logger(__name__)


class MarketResearchOutput(BaseModel):
    """Validated output schema for market research."""
    
    asset: str = Field(..., description="Asset symbol")
    risk_level: str = Field(..., description="Risk level: Low, Medium, or High")
    sentiment_score: float = Field(..., ge=0.0, le=1.0, description="Sentiment score between 0 and 1")
    tools_used: List[str] = Field(..., description="List of tools used by the agent")
    analysis: Optional[str] = Field(None, description="Brief analysis explanation")
    
    def validate_risk_level(self) -> "MarketResearchOutput":
        """Validate risk level is one of the allowed values."""
        if self.risk_level not in ["Low", "Medium", "High"]:
            raise ValueError(f"Invalid risk_level: {self.risk_level}. Must be Low, Medium, or High")
        return self


class MarketResearchAgent:
    """AI agent for conducting market research analysis."""
    
    def __init__(self):
        """Initialize the market research agent."""
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7,
            max_tokens=2000,
        )
        self.tools = self._create_langchain_tools()
        self.agent_executor = self._create_agent()
        
    def _create_langchain_tools(self) -> List[Tool]:
        """
        Returns list of LangChain Tool instances
        """
        langchain_tools = []
        for tool in AVAILABLE_TOOLS:
            langchain_tool = Tool(
                name=tool.name,
                description=tool.description,
                func=lambda asset, t=tool: json.dumps(t.execute(asset))
            )
            langchain_tools.append(langchain_tool)
        return langchain_tools
    
    def _create_agent(self) -> AgentExecutor:
        """
        Returns Configured AgentExecutor
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            return_intermediate_steps=True,
        )
    
    def research(self, asset: str, max_retries: int = 3) -> Dict[str, Any]:
        """Conduct market research for an asset.
        
        Args:
            asset: Asset symbol to research
            max_retries: Maximum number of retry attempts for validation failures
            
        Returns Research results with execution metadata
            
        Raises Exception If research fails after all retries
        """
        start_time = time.time()
        agent_steps = []
        tool_calls = []
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting research for {asset} (attempt {attempt + 1}/{max_retries})")
                
                prompt = get_research_prompt(asset)
                result = self.agent_executor.invoke({"input": prompt})
                
                if "intermediate_steps" in result:
                    for step in result["intermediate_steps"]:
                        action, observation = step
                        tool_calls.append({
                            "tool": action.tool,
                            "input": action.tool_input,
                            "output": observation
                        })
                        agent_steps.append({
                            "action": action.tool,
                            "thought": action.log if hasattr(action, 'log') else ""
                        })
                
                output_text = result.get("output", "")
                logger.info(f"Agent output: {output_text}")
                
                validated_output = self._parse_and_validate_output(output_text, asset)
                
                execution_time = (time.time() - start_time) * 1000
                
                return {
                    "output": validated_output,
                    "agent_steps": agent_steps,
                    "tool_calls": tool_calls,
                    "execution_time_ms": execution_time,
                    "success": True,
                    "error": None
                }
                
            except ValidationError as e:
                logger.warning(f"Validation error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    execution_time = (time.time() - start_time) * 1000
                    raise Exception(f"Failed to generate valid output after {max_retries} attempts: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error during research: {e}")
                execution_time = (time.time() - start_time) * 1000
                raise
        
        raise Exception("Research failed unexpectedly")
    
    def _parse_and_validate_output(self, output_text: str, asset: str) -> Dict[str, Any]:
        """
        Args:
            output_text: Raw output from agent
            asset: Expected asset symbol
            
        Returns:
            Validated output dictionary
            
        Raises:
            ValidationError: If output is invalid
        """
        try:
            output_dict = json.loads(output_text)
        except json.JSONDecodeError:
            start_idx = output_text.find('{')
            end_idx = output_text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = output_text[start_idx:end_idx + 1]
                output_dict = json.loads(json_str)
            else:
                raise ValueError("Could not find valid JSON in agent output")
        
        validated = MarketResearchOutput(**output_dict)
        validated.validate_risk_level()
        
        if validated.asset.upper() != asset.upper():
            validated.asset = asset.upper()
        
        return validated.model_dump()


market_agent = MarketResearchAgent()
