"""
Goal Planning Agent - Projects financial goals and calculates required savings

This agent analyzes current financial situations and projects timelines/savings
needed to reach financial goals using compound interest calculations.
"""

import math
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from src.agents import BaseAgent, AgentOutput
from src.core.market_data import get_market_data_provider
from src.core.portfolio_calc import get_portfolio_calculator
from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GoalProjection:
    """Financial goal projection metrics"""
    current_value: float
    goal_amount: float
    time_horizon_years: float
    gap: float
    required_annual_return: float
    required_monthly_contribution: float
    projected_value_with_contributions: float
    projected_months_to_goal: float
    risk_level: str  # low|moderate|high
    allocation_suggestion: Dict[str, float]  # {"stocks": 60, "bonds": 40}


class GoalPlanningAgent(BaseAgent):
    """
    Analyzes financial goals and projects required savings/returns.
    
    Uses compound interest formulas to calculate:
    - Monthly contributions needed
    - Time to reach goal
    - Required annual returns
    - Recommended asset allocation based on time horizon
    """

    def __init__(self):
        """Initialize Goal Planning Agent"""
        super().__init__("goal_planning")
        self.market_data_provider = get_market_data_provider()
        self.portfolio_calc = get_portfolio_calculator()

    async def execute(
        self,
        user_message: str,
        goal_data: Optional[Dict[str, Any]] = None
    ) -> AgentOutput:
        """
        Execute goal planning analysis
        
        Args:
            user_message: User's goal planning question
            goal_data: Dict with:
                - current_value: float (current portfolio/savings)
                - goal_amount: float (target amount)
                - time_horizon_years: float (years to reach goal)
                - risk_appetite: str ("low"|"moderate"|"high")
                - monthly_budget: Optional[float] (if specified)
                - current_return: Optional[float] (assumed annual return %)
        
        Returns:
            AgentOutput with projections and recommendations
        """
        self._log_execution("START", f"goal_planning - {user_message[:50]}")

        try:
            # Parse goal data
            if not goal_data:
                goal_data = {}

            current_value = goal_data.get("current_value", 0)
            goal_amount = goal_data.get("goal_amount", 100000)
            time_horizon_years = goal_data.get("time_horizon_years", 5)
            risk_appetite = goal_data.get("risk_appetite", "moderate")
            monthly_budget = goal_data.get("monthly_budget")
            assumed_return = goal_data.get("current_return", self._get_default_return(risk_appetite))

            # Validate inputs
            if goal_amount <= 0:
                return AgentOutput(
                    answer_text="Goal amount must be positive.",
                    structured_data={},
                    citations=[],
                    tool_calls_made=[]
                )

            if time_horizon_years <= 0:
                return AgentOutput(
                    answer_text="Time horizon must be greater than 0.",
                    structured_data={},
                    citations=[],
                    tool_calls_made=[]
                )

            # Calculate projections
            projections = self._calculate_goal_projections(
                current_value=current_value,
                goal_amount=goal_amount,
                time_horizon_years=time_horizon_years,
                risk_appetite=risk_appetite,
                assumed_annual_return=assumed_return,
                monthly_budget=monthly_budget
            )

            # Generate narrative
            narrative = self._generate_goal_narrative(
                user_message=user_message,
                projections=projections
            )

            self._log_execution("SUCCESS", f"goal_planning - Generated projections")

            return AgentOutput(
                answer_text=narrative,
                structured_data=self._projections_to_dict(projections),
                citations=[],
                tool_calls_made=["portfolio_calculation", "goal_projection"]
            )

        except Exception as e:
            self._log_execution("ERROR", f"goal_planning error: {str(e)}")
            return AgentOutput(
                answer_text=f"Error in goal planning: {str(e)}",
                structured_data={},
                citations=[],
                tool_calls_made=[]
            )

    def _get_default_return(self, risk_appetite: str) -> float:
        """Get default annual return based on risk appetite"""
        return {
            "low": 3.0,  # 3% bonds/stable
            "moderate": 6.0,  # 6% balanced portfolio
            "high": 8.5  # 8.5% equity-heavy
        }.get(risk_appetite, 6.0)

    def _calculate_goal_projections(
        self,
        current_value: float,
        goal_amount: float,
        time_horizon_years: float,
        risk_appetite: str,
        assumed_annual_return: float,
        monthly_budget: Optional[float] = None
    ) -> GoalProjection:
        """
        Calculate goal projections using compound interest
        
        Formulas:
        - Future Value = PV * (1 + r)^t + PMT * [((1 + r)^t - 1) / r]
        - Required PMT = (FV - PV*(1+r)^t) / [((1 + r)^t - 1) / r]
        - Required Return = (FV / PV)^(1/t) - 1
        """
        gap = goal_amount - current_value
        monthly_rate = assumed_annual_return / 100 / 12
        total_months = time_horizon_years * 12

        # If no monthly budget specified, calculate required contribution
        if monthly_budget is None:
            if gap <= 0:
                # Already at goal
                required_monthly = 0
            else:
                # Calculate required monthly contribution
                future_value_of_current = current_value * (1 + monthly_rate) ** total_months
                remaining_gap = goal_amount - future_value_of_current

                if remaining_gap <= 0:
                    required_monthly = 0
                else:
                    # PMT = FV / [((1 + r)^n - 1) / r]
                    annuity_factor = ((1 + monthly_rate) ** total_months - 1) / monthly_rate
                    required_monthly = remaining_gap / annuity_factor
        else:
            required_monthly = monthly_budget

        # Calculate projected value with contributions
        future_current = current_value * (1 + monthly_rate) ** total_months
        annuity_factor = ((1 + monthly_rate) ** total_months - 1) / monthly_rate
        future_contributions = required_monthly * annuity_factor
        projected_value = future_current + future_contributions

        # Calculate projected months to reach goal (if using specified budget)
        if monthly_budget:
            projected_months = self._calculate_months_to_goal(
                current_value, goal_amount, monthly_budget, monthly_rate
            )
        else:
            projected_months = total_months

        # Get allocation suggestion based on time horizon
        allocation = self._get_allocation_by_horizon(time_horizon_years)

        return GoalProjection(
            current_value=current_value,
            goal_amount=goal_amount,
            time_horizon_years=time_horizon_years,
            gap=gap,
            required_annual_return=assumed_annual_return,
            required_monthly_contribution=required_monthly,
            projected_value_with_contributions=projected_value,
            projected_months_to_goal=projected_months,
            risk_level=risk_appetite,
            allocation_suggestion=allocation
        )

    def _calculate_months_to_goal(
        self,
        current: float,
        goal: float,
        monthly_contribution: float,
        monthly_rate: float
    ) -> float:
        """Calculate months needed to reach goal with fixed monthly contribution"""
        if monthly_contribution <= 0:
            return float('inf')

        # Binary search for months
        months = 1
        max_iterations = 600  # 50 years max
        tolerance = 100  # $100 tolerance

        for _ in range(max_iterations):
            future_value = (
                current * (1 + monthly_rate) ** months +
                monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            )

            if abs(future_value - goal) < tolerance:
                return months

            if future_value < goal:
                months += 1
            else:
                break

        return months

    def _get_allocation_by_horizon(self, years: float) -> Dict[str, float]:
        """Get suggested asset allocation based on time horizon"""
        # Rule of thumb: More aggressive if longer horizon
        # Short-term (<3 years) = conservative to moderate
        # Medium-term (3-7 years) = balanced
        # Long-term (7+ years) = aggressive
        if years >= 10:
            return {"stocks": 85, "bonds": 10, "cash": 5}
        elif years >= 7:
            return {"stocks": 80, "bonds": 15, "cash": 5}
        elif years >= 5:
            return {"stocks": 70, "bonds": 25, "cash": 5}
        elif years >= 3:
            return {"stocks": 60, "bonds": 35, "cash": 5}
        else:
            return {"stocks": 40, "bonds": 45, "cash": 15}

    def _generate_goal_narrative(
        self,
        user_message: str,
        projections: GoalProjection
    ) -> str:
        """Generate narrative report for goal projections"""
        gap_pct = (projections.gap / projections.goal_amount * 100) if projections.goal_amount else 0

        # Timeline assessment
        years_to_goal = projections.projected_months_to_goal / 12
        timeline_assessment = (
            f"✅ You'll reach your goal in **{years_to_goal:.1f} years** "
            f"({projections.projected_months_to_goal:.0f} months)"
            if projections.projected_months_to_goal < float('inf') and projections.projected_months_to_goal > 0
            else "⚠️ Current savings don't reach goal without additional contributions"
        )

        # Required contribution assessment
        if projections.required_monthly_contribution > 0:
            contribution_message = (
                f"📊 You need to save **${projections.required_monthly_contribution:,.2f}/month** "
                f"to reach your goal in {projections.time_horizon_years} years"
            )
        else:
            contribution_message = "✨ You're already on track to reach your goal!"

        # Risk allocation message
        allocation = projections.allocation_suggestion
        allocation_msg = (
            f"**Recommended Allocation** (based on {projections.time_horizon_years}-year horizon):\n"
            f"- 📈 Stocks: {allocation['stocks']}%\n"
            f"- 🏦 Bonds: {allocation['bonds']}%\n"
            f"- 💰 Cash: {allocation['cash']}%"
        )

        return f"""## Financial Goal Projection

### Your Goal
- **Target Amount:** ${projections.goal_amount:,.2f}
- **Current Value:** ${projections.current_value:,.2f}
- **Gap:** ${projections.gap:,.2f} ({gap_pct:.1f}%)
- **Time Horizon:** {projections.time_horizon_years} years
- **Risk Level:** {projections.risk_level.upper()}

### Projections
{contribution_message}

**Assumed Annual Return:** {projections.required_annual_return}%

{timeline_assessment}

**Projected Value in {projections.time_horizon_years} years:** ${projections.projected_value_with_contributions:,.2f}

### Asset Allocation Strategy

{allocation_msg}

### Key Insights

1. **Monthly Savings:** Consistent monthly contributions are the most powerful tool. Even small increases compound significantly over time.

2. **Return Assumptions:** We assume {projections.required_annual_return}% annual return based on your {projections.risk_level} risk appetite. Actual returns vary.

3. **Sensitivity:** This analysis is based on average returns. Markets fluctuate - consider best/worst case scenarios.

4. **Rebalancing:** Review and rebalance your portfolio annually to maintain your target allocation.

5. **Inflation:** Remember to account for inflation when setting your goal amount.

### Next Steps
- Set up automatic monthly contributions if possible
- Adjust allocation based on your comfort with volatility
- Review progress quarterly
- Consult a financial advisor for personalized guidance
"""

    @staticmethod
    def _projections_to_dict(projections: GoalProjection) -> Dict[str, Any]:
        """Convert GoalProjection dataclass to dictionary"""
        return {
            "current_value": projections.current_value,
            "goal_amount": projections.goal_amount,
            "time_horizon_years": projections.time_horizon_years,
            "gap": projections.gap,
            "gap_percentage": (projections.gap / projections.goal_amount * 100) if projections.goal_amount else 0,
            "required_annual_return": projections.required_annual_return,
            "required_monthly_contribution": projections.required_monthly_contribution,
            "projected_value_with_contributions": projections.projected_value_with_contributions,
            "projected_months_to_goal": projections.projected_months_to_goal,
            "projected_years_to_goal": projections.projected_months_to_goal / 12,
            "risk_level": projections.risk_level,
            "allocation_suggestion": projections.allocation_suggestion
        }


# Singleton instance
_goal_planning_agent: Optional[GoalPlanningAgent] = None


def get_goal_planning_agent() -> GoalPlanningAgent:
    """Get or create Goal Planning Agent singleton"""
    global _goal_planning_agent
    if _goal_planning_agent is None:
        _goal_planning_agent = GoalPlanningAgent()
    return _goal_planning_agent
