"""
Agent Executor for Multi-Agent Orchestration

Handles execution of individual agents and manages their outputs.
Supports parallel and sequential execution strategies.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from src.orchestration.state import (
    OrchestrationState, AgentType, AgentExecution, Intent
)
from src.agents.finance_qa import get_finance_qa_agent
from src.agents.portfolio_analysis import get_portfolio_analysis_agent
from src.agents.market_analysis import get_market_analysis_agent
from src.agents.goal_planning import get_goal_planning_agent
from src.agents.tax_education import get_tax_education_agent
from src.agents.news_synthesizer import get_news_synthesizer_agent
from src.core.logger import get_logger


logger = get_logger(__name__)


class AgentExecutor:
    """
    Executes agents based on routing decisions
    
    Manages:
    - Individual agent calls
    - Parallel/sequential execution
    - Output collection
    - Error handling
    """
    
    def __init__(self):
        """Initialize executor with agent instances"""
        self.agents_map = {
            AgentType.FINANCE_QA: get_finance_qa_agent(),
            AgentType.PORTFOLIO_ANALYSIS: get_portfolio_analysis_agent(),
            AgentType.MARKET_ANALYSIS: get_market_analysis_agent(),
            AgentType.GOAL_PLANNING: get_goal_planning_agent(),
            AgentType.TAX_EDUCATION: get_tax_education_agent(),
            AgentType.NEWS_SYNTHESIZER: get_news_synthesizer_agent(),
        }
    
    async def execute_agent(
        self,
        agent_type: AgentType,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a single agent
        
        Args:
            agent_type: Type of agent to execute
            user_input: User's input/query
            context: Additional context (extracted tickers, amounts, etc.)
            
        Returns:
            Agent output or error dict
        """
        if context is None:
            context = {}
        
        start_time = time.time()
        
        try:
            agent = self.agents_map[agent_type]
            
            # Build agent input with context
            agent_input = user_input
            if context.get("tickers"):
                agent_input += f"\n[Context: Tickers: {', '.join(context['tickers'])}]"
            if context.get("amounts"):
                agent_input += f"\n[Context: Amounts: {context['amounts']}]"
            if context.get("timeframe"):
                agent_input += f"\n[Context: Timeframe: {context['timeframe']}]"
            
            # Execute agent using execute() method
            output = await agent.execute(agent_input)
            
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(
                f"Agent {agent_type.value} completed in {execution_time:.1f}ms"
            )
            
            return {
                "status": "success",
                "output": output,
                "execution_time_ms": execution_time,
                "agent": agent_type.value
            }
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Agent {agent_type.value} failed: {str(e)}"
            
            logger.error(error_msg, exc_info=True)
            
            return {
                "status": "error",
                "error": error_msg,
                "execution_time_ms": execution_time,
                "agent": agent_type.value
            }
    
    async def execute_agents_parallel(
        self,
        agents: List[AgentType],
        user_input: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute multiple agents in parallel
        
        Args:
            agents: List of agents to execute
            user_input: User's input/query
            context: Additional context
            
        Returns:
            Dict mapping agent type to execution result
        """
        tasks = [
            self.execute_agent(agent, user_input, context)
            for agent in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        output = {}
        for agent, result in zip(agents, results):
            output[agent.value] = result
        
        return output
    
    async def execute_agents_sequential(
        self,
        agents: List[AgentType],
        user_input: str,
        context: Dict[str, Any] = None,
        shared_outputs: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute agents sequentially
        
        Useful when later agents depend on outputs from earlier agents.
        
        Args:
            agents: List of agents to execute
            user_input: User's input/query
            context: Additional context
            shared_outputs: If True, each agent sees outputs from previous agents
            
        Returns:
            Dict mapping agent type to execution result
        """
        output = {}
        current_context = context.copy() if context else {}
        
        for agent in agents:
            result = await self.execute_agent(agent, user_input, current_context)
            output[agent.value] = result
            
            # If shared outputs enabled, add this result to context for next agent
            if shared_outputs and result["status"] == "success":
                # Extract key metrics from output
                agent_output = result.get("output", {})
                if isinstance(agent_output, dict):
                    current_context[f"{agent.value}_output"] = agent_output
        
        return output
    
    async def execute(
        self,
        state: OrchestrationState,
        parallel: bool = True
    ) -> OrchestrationState:
        """
        Execute agents based on orchestration state
        
        Args:
            state: Current orchestration state
            parallel: Whether to execute agents in parallel (default True)
            
        Returns:
            Updated orchestration state with execution results
        """
        if not state.selected_agents:
            logger.warning("No agents selected for execution")
            state.add_error("No agents selected")
            return state
        
        # Prepare context from extracted data
        context = {
            "tickers": state.extracted_tickers,
            "amounts": getattr(state, 'extracted_amounts', []),
            "timeframe": getattr(state, 'extracted_timeframe', None),
        }
        
        state.workflow_state = "execution"
        
        logger.info(
            f"Executing {len(state.selected_agents)} agent(s) "
            f"({'parallel' if parallel else 'sequential'})"
        )
        
        # Execute agents
        if parallel and len(state.selected_agents) > 1:
            results = await self.execute_agents_parallel(
                state.selected_agents,
                state.user_input,
                context
            )
        else:
            results = await self.execute_agents_sequential(
                state.selected_agents,
                state.user_input,
                context,
                shared_outputs=True
            )
        
        # Process results
        for agent_type, result in results.items():
            state.agent_outputs[agent_type] = result
            
            execution_record = AgentExecution(
                agent_type=AgentType(agent_type),
                user_input=state.user_input,
                output=result,
                status=result.get("status", "error"),
                execution_time_ms=result.get("execution_time_ms", 0),
                error=result.get("error")
            )
            state.add_agent_execution(execution_record)
        
        logger.info(f"Agent execution complete. Results: {list(results.keys())}")
        
        return state


# Singleton instance
_executor = None


def get_agent_executor() -> AgentExecutor:
    """Get singleton instance of agent executor"""
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
    return _executor
