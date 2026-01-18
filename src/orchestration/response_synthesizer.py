"""
Response Synthesizer for Multi-Agent Orchestration

Combines outputs from multiple agents into a coherent, synthesized response.
Handles conflict resolution, formatting, and output structuring.
"""

import logging
from typing import List, Dict, Any, Optional
from src.orchestration.state import (
    OrchestrationState, Intent, SynthesisResult, AgentType
)
from src.core.llm_provider import get_llm_provider
from src.core.logger import get_logger


logger = get_logger(__name__)


class ResponseSynthesizer:
    """
    Synthesizes responses from multiple agents into a single coherent output
    
    Responsibilities:
    - Merge outputs from multiple agents
    - Generate cohesive narrative response
    - Structure output for readability
    - Handle conflicts or contradictions
    - Extract key insights and recommendations
    """
    
    def __init__(self):
        """Initialize synthesizer with LLM provider"""
        self.llm = get_llm_provider()
    
    def _extract_response_text(self, agent_output: Dict[str, Any]) -> str:
        """
        Extract readable response text from agent output
        
        Agent outputs come in different formats, so this normalizes them
        """
        if not agent_output:
            return ""
        
        # Direct text response
        if isinstance(agent_output, str):
            return agent_output
        
        # AgentOutput dataclass format
        if hasattr(agent_output, "response"):
            return str(agent_output.response)
        
        # Dict with 'response' key
        if isinstance(agent_output, dict):
            if "response" in agent_output:
                return str(agent_output["response"])
            if "output" in agent_output:
                return str(agent_output["output"])
            if "text" in agent_output:
                return str(agent_output["text"])
        
        # Fallback: convert to string
        return str(agent_output)
    
    def _extract_structured_data(
        self,
        agent_type: AgentType,
        agent_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data from agent output
        
        Different agents return different structured data types
        """
        if not agent_output:
            return {}
        
        structured = {}
        
        # Portfolio Analysis - Extract metrics
        if agent_type == AgentType.PORTFOLIO_ANALYSIS:
            if hasattr(agent_output, "data") and isinstance(agent_output.data, dict):
                structured = agent_output.data
            elif isinstance(agent_output, dict):
                # Extract allocation, diversification, etc.
                for key in ["allocation", "diversification", "concentration", "metrics"]:
                    if key in agent_output:
                        structured[key] = agent_output[key]
        
        # Market Analysis - Extract quotes
        elif agent_type == AgentType.MARKET_ANALYSIS:
            if isinstance(agent_output, dict):
                for key in ["quotes", "data", "market_data", "historical"]:
                    if key in agent_output:
                        structured[key] = agent_output[key]
        
        # Goal Planning - Extract projections
        elif agent_type == AgentType.GOAL_PLANNING:
            if isinstance(agent_output, dict):
                for key in ["projection", "monthly_contribution", "timeline", "target"]:
                    if key in agent_output:
                        structured[key] = agent_output[key]
        
        return structured
    
    def synthesize_single_agent(
        self,
        state: OrchestrationState,
        agent_type: AgentType
    ) -> str:
        """
        Synthesize response when only one agent was used
        
        Args:
            state: Orchestration state with agent outputs
            agent_type: The single agent that was executed
            
        Returns:
            Synthesized response string
        """
        agent_output = state.agent_outputs.get(agent_type.value, {})
        
        if agent_output.get("status") == "error":
            return (
                f"I encountered an error while processing your request: "
                f"{agent_output.get('error', 'Unknown error')}. "
                f"Please try rephrasing your question."
            )
        
        output = agent_output.get("output", {})
        response_text = self._extract_response_text(output)
        
        return response_text if response_text else (
            "I was unable to generate a response for your query. "
            "Please try rephrasing or provide more specific information."
        )
    
    def synthesize_multi_agent(
        self,
        state: OrchestrationState
    ) -> str:
        """
        Synthesize response from multiple agents
        
        Combines outputs coherently based on the type of analysis
        """
        sections = []
        
        # Group agents by category
        portfolio_agents = []
        market_agents = []
        planning_agents = []
        education_agents = []
        
        for agent_type in state.selected_agents:
            if agent_type == AgentType.PORTFOLIO_ANALYSIS:
                portfolio_agents.append(agent_type)
            elif agent_type == AgentType.MARKET_ANALYSIS:
                market_agents.append(agent_type)
            elif agent_type == AgentType.GOAL_PLANNING:
                planning_agents.append(agent_type)
            else:
                education_agents.append(agent_type)
        
        # Process portfolio analysis
        if portfolio_agents:
            for agent_type in portfolio_agents:
                agent_output = state.agent_outputs.get(agent_type.value, {})
                if agent_output.get("status") == "success":
                    response = self._extract_response_text(agent_output.get("output", {}))
                    if response:
                        sections.append(f"**Portfolio Analysis:**\n{response}")
        
        # Process market analysis
        if market_agents:
            for agent_type in market_agents:
                agent_output = state.agent_outputs.get(agent_type.value, {})
                if agent_output.get("status") == "success":
                    response = self._extract_response_text(agent_output.get("output", {}))
                    if response:
                        sections.append(f"**Market Data:**\n{response}")
        
        # Process planning
        if planning_agents:
            for agent_type in planning_agents:
                agent_output = state.agent_outputs.get(agent_type.value, {})
                if agent_output.get("status") == "success":
                    response = self._extract_response_text(agent_output.get("output", {}))
                    if response:
                        sections.append(f"**Financial Projections:**\n{response}")
        
        # Process education/tax
        if education_agents:
            for agent_type in education_agents:
                agent_output = state.agent_outputs.get(agent_type.value, {})
                if agent_output.get("status") == "success":
                    response = self._extract_response_text(agent_output.get("output", {}))
                    if response:
                        label = "Tax Information" if agent_type == AgentType.TAX_EDUCATION else "Information"
                        sections.append(f"**{label}:**\n{response}")
        
        # Join sections with blank lines
        if sections:
            return "\n\n".join(sections)
        else:
            # Handle case where all agents failed
            errors = [
                state.agent_outputs.get(agent.value, {}).get("error", "Unknown error")
                for agent in state.selected_agents
            ]
            return (
                f"I encountered errors while processing your request:\n" +
                "\n".join([f"- {e}" for e in errors if e]) +
                "\n\nPlease try rephrasing your question."
            )
    
    def build_response_structure(
        self,
        state: OrchestrationState
    ) -> Dict[str, str]:
        """
        Build structured response with labeled sections
        
        Returns dict mapping section names to content
        """
        structure = {}
        
        for agent_type in state.selected_agents:
            agent_output = state.agent_outputs.get(agent_type.value, {})
            
            if agent_output.get("status") == "success":
                response = self._extract_response_text(agent_output.get("output", {}))
                
                section_name = {
                    AgentType.FINANCE_QA: "Educational Content",
                    AgentType.PORTFOLIO_ANALYSIS: "Portfolio Analysis",
                    AgentType.MARKET_ANALYSIS: "Market Data",
                    AgentType.GOAL_PLANNING: "Financial Projections",
                    AgentType.TAX_EDUCATION: "Tax Information",
                    AgentType.NEWS_SYNTHESIZER: "Market News & Sentiment",
                }.get(agent_type, "Analysis")
                
                if response:
                    structure[section_name] = response
        
        return structure
    
    def extract_key_insights(
        self,
        state: OrchestrationState
    ) -> List[str]:
        """
        Extract key insights from agent outputs
        
        Identifies actionable insights and important data points
        """
        insights = []
        
        # Extract from portfolio analysis
        for agent_output in state.agent_outputs.values():
            if agent_output.get("status") == "success":
                output = agent_output.get("output", {})
                
                # Look for structured metrics
                if isinstance(output, dict):
                    # Diversification score
                    if "diversification" in output:
                        div_score = output["diversification"]
                        if isinstance(div_score, (int, float)):
                            insights.append(
                                f"Diversification score: {div_score}/100"
                            )
                    
                    # Key metrics
                    if "total_value" in output:
                        insights.append(f"Portfolio value: ${output['total_value']}")
        
        return insights[:5]  # Limit to top 5 insights
    
    def extract_recommendations(
        self,
        state: OrchestrationState
    ) -> List[str]:
        """
        Extract recommendations from agent outputs
        
        Identifies action items and recommendations
        """
        recommendations = []
        
        # Check for specific recommendation patterns in responses
        for agent_output in state.agent_outputs.values():
            if agent_output.get("status") == "success":
                output_text = self._extract_response_text(agent_output.get("output", {}))
                
                # Look for recommendation keywords
                if "recommend" in output_text.lower() or "should" in output_text.lower():
                    # Extract sentence containing recommendation
                    sentences = output_text.split(".")
                    for sentence in sentences:
                        if "recommend" in sentence.lower() or "should" in sentence.lower():
                            clean = sentence.strip()
                            if clean and len(clean) > 10:
                                recommendations.append(clean)
                                break
        
        return recommendations[:3]  # Limit to top 3
    
    async def synthesize(self, state: OrchestrationState) -> OrchestrationState:
        """
        Main synthesis method
        
        Combines all agent outputs into a coherent response
        
        Args:
            state: Orchestration state with agent execution results
            
        Returns:
            Updated state with synthesized response
        """
        state.workflow_state = "synthesis"
        
        logger.info(f"Synthesizing response from {len(state.selected_agents)} agent(s)")
        
        # Determine synthesis approach based on number of agents
        if len(state.selected_agents) == 1:
            response = self.synthesize_single_agent(state, state.selected_agents[0])
        else:
            response = self.synthesize_multi_agent(state)
        
        # Build response structure
        structure = self.build_response_structure(state)
        
        # Extract insights and recommendations
        insights = self.extract_key_insights(state)
        recommendations = self.extract_recommendations(state)
        
        state.synthesized_response = response
        state.response_structure = structure
        
        # Store for potential API access
        state.debug_info["key_insights"] = insights
        state.debug_info["recommendations"] = recommendations
        
        state.workflow_state = "complete"
        
        logger.info("Response synthesis complete")
        
        return state


# Singleton instance
_synthesizer = None


def get_response_synthesizer() -> ResponseSynthesizer:
    """Get singleton instance of response synthesizer"""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = ResponseSynthesizer()
    return _synthesizer
