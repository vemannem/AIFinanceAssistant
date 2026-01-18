import { useState, useEffect } from 'react';
import { agentsService } from '@/services/agentsService';
import { useSettingsStore } from '@/store/settingsStore';
import { useLangGraphStore } from '@/store/langgraphStore';
import { ExecutionMetrics } from '@/types';

export function GoalPlanningView() {
  const settingsStore = useSettingsStore();
  const langgraphStore = useLangGraphStore();
  const [currentValue, setCurrentValue] = useState('10000');
  const [goalAmount, setGoalAmount] = useState('100000');
  const [timeHorizon, setTimeHorizon] = useState('10');
  const [riskAppetite, setRiskAppetite] = useState(settingsStore.settings.riskAppetite);
  const [annualReturn, setAnnualReturn] = useState('6.0');
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRiskAppetite(settingsStore.settings.riskAppetite);
  }, [settingsStore.settings.riskAppetite]);

  const handlePlanGoal = async () => {
    try {
      setLoading(true);
      setError(null);
      langgraphStore.setLoading(true);  // Set LangGraph store loading state

      const current = parseFloat(currentValue);
      const goal = parseFloat(goalAmount);
      const years = parseFloat(timeHorizon);
      const returnRate = parseFloat(annualReturn);

      if (isNaN(current) || isNaN(goal) || isNaN(years) || isNaN(returnRate)) {
        setError('Please enter valid numbers for all fields');
        return;
      }

      if (years <= 0) {
        setError('Time horizon must be greater than 0');
        return;
      }

      const result = await agentsService.planGoals(
        current,
        goal,
        years,
        undefined,
        riskAppetite,
        returnRate
      );

      setPlan(result);

      // Update LangGraph execution state for StateGraph display
      const executionMetrics: ExecutionMetrics = {
        confidence: result.confidence ?? 0.8,
        intent: result.intent ?? 'goal_planning',
        agentsUsed: result.agents_used ?? ['goal_planning'],
        executionTimes: result.execution_times ?? {},
        totalTimeMs: result.total_time_ms ?? 0,
      };

      langgraphStore.setExecution({
        ...executionMetrics,
        message: result.message,
        timestamp: new Date(),
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Planning failed';
      setError(errorMsg);
    } finally {
      setLoading(false);
      langgraphStore.setLoading(false);  // Clear LangGraph store loading state
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Goal Planning</h2>
        <p className="text-gray-600">Plan your financial goals with projections and recommendations</p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current Value ($)
            </label>
            <input
              type="number"
              value={currentValue}
              onChange={(e) => setCurrentValue(e.target.value)}
              placeholder="10000"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Goal Amount ($)
            </label>
            <input
              type="number"
              value={goalAmount}
              onChange={(e) => setGoalAmount(e.target.value)}
              placeholder="100000"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Horizon (Years)
            </label>
            <input
              type="number"
              value={timeHorizon}
              onChange={(e) => setTimeHorizon(e.target.value)}
              placeholder="10"
              step="0.5"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Expected Annual Return (%)
            </label>
            <input
              type="number"
              value={annualReturn}
              onChange={(e) => setAnnualReturn(e.target.value)}
              placeholder="6.0"
              step="0.1"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Risk Appetite
          </label>
          <select
            value={riskAppetite}
            onChange={(e) => setRiskAppetite(e.target.value as 'low' | 'moderate' | 'high')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="low">Low (Conservative)</option>
            <option value="moderate">Moderate (Balanced)</option>
            <option value="high">High (Aggressive)</option>
          </select>
        </div>

        <button
          onClick={handlePlanGoal}
          disabled={loading}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {loading ? 'Planning...' : 'Plan Goal'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Plan Results */}
      {plan && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-xl font-bold text-gray-900">📊 Your Goal Plan</h3>
          
          {/* Main message */}
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap max-h-96 overflow-y-auto">
            {plan.message}
          </div>

          {/* Structured data if available */}
          {plan.structured_data && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">💰 Detailed Plan</h4>
              
              {/* Key metrics grid */}
              {plan.structured_data.monthly_contribution && (
                <div className="grid grid-cols-2 gap-4 mb-6 bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <div>
                    <p className="text-sm text-gray-600">Monthly Savings Needed</p>
                    <p className="text-2xl font-bold text-blue-600">${parseFloat(plan.structured_data.monthly_contribution).toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Projected Value</p>
                    <p className="text-2xl font-bold text-green-600">${parseFloat(plan.structured_data.projected_value).toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Contribution Total</p>
                    <p className="text-2xl font-bold text-purple-600">${parseFloat(plan.structured_data.total_contributed).toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Investment Gain</p>
                    <p className="text-2xl font-bold text-orange-600">${parseFloat(plan.structured_data.investment_gain).toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
                  </div>
                </div>
              )}

              {/* Collapsible JSON view */}
              <details className="cursor-pointer">
                <summary className="font-medium text-gray-700 hover:text-gray-900 bg-gray-50 p-3 rounded border border-gray-200">
                  📋 View all calculations (JSON)
                </summary>
                <div className="mt-3 bg-gray-900 text-gray-100 rounded border border-gray-700 overflow-hidden">
                  <pre className="text-xs p-4 overflow-x-auto max-h-96 overflow-y-auto font-mono leading-relaxed">
                    {JSON.stringify(plan.structured_data, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}

          {/* Citations */}
          {plan.citations && plan.citations.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-3">📚 Resources</h4>
              <ul className="space-y-2">
                {plan.citations.map((citation: any, idx: number) => (
                  <li key={idx} className="text-sm">
                    <a
                      href={citation.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {citation.title}
                    </a>
                    {citation.category && (
                      <span className="ml-2 text-gray-500 text-xs">({citation.category})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!plan && !loading && (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">Fill in your goal details and click "Plan Goal" to get started</p>
        </div>
      )}
    </div>
  );
}
