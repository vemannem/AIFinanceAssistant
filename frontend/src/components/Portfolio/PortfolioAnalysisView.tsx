import { useState, useEffect } from 'react';
import { orchestrationService } from '@/services/orchestrationService';
import { usePortfolioStore } from '@/store/portfolioStore';
import { useSettingsStore } from '@/store/settingsStore';
import { useLangGraphStore } from '@/store/langgraphStore';

export function PortfolioAnalysisView() {
  const { holdings } = usePortfolioStore();
  useSettingsStore.getState().loadSettings();
  const langgraphStore = useLangGraphStore();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load settings when component mounts
    useSettingsStore.getState().loadSettings();
  }, []);

  const handleAnalyze = async (analysisType: string = 'full') => {
    try {
      setLoading(true);
      setError(null);
      langgraphStore.setLoading(true);

      if (holdings.length === 0) {
        setError('Please add holdings to your portfolio first');
        return;
      }

      // Build query for portfolio analysis with specific keywords based on analysis type
      const tickerList = holdings.map(h => h.ticker).join(', ');
      
      // Create intent-specific messages to help router select correct agent
      let query: string;
      if (analysisType === 'allocation' || analysisType === 'diversification' || analysisType === 'rebalance') {
        query = `Portfolio allocation and diversification analysis for my holdings: ${tickerList}. Analyze allocation percentages, diversification score, and rebalancing recommendations.`;
      } else if (analysisType === 'tax') {
        query = `Tax impact analysis for my portfolio holdings: ${tickerList}. Calculate capital gains, tax liability, and tax loss harvesting opportunities.`;
      } else if (analysisType === 'dividend') {
        query = `Dividend analysis for my portfolio: ${tickerList}. Calculate dividend yields, income, and dividend growth potential.`;
      } else if (analysisType === 'full') {
        query = `Comprehensive portfolio analysis for my holdings: ${tickerList}. Include allocation, diversification, risk assessment, and recommendations.`;
      } else {
        query = `Analyze my portfolio with tickers: ${tickerList} for ${analysisType} analysis`;
      }

      // Use orchestration service to go through LangGraph router
      const result = await orchestrationService.sendMessage(
        query,
        undefined,
        []
      );

      setAnalysis(result);

      // Update LangGraph execution state with full metadata from orchestration
      langgraphStore.setExecution({
        confidence: result.confidence || 0.8,
        intent: result.intent,
        agentsUsed: result.agents_used || [],
        executionTimes: result.execution_times || {},
        totalTimeMs: result.total_time_ms || 0,
        metadata: result.metadata, // ✅ INCLUDES execution_details and workflow_analysis
        message: result.message,
        timestamp: new Date(),
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Analysis failed';
      setError(errorMsg);
    } finally {
      setLoading(false);
      langgraphStore.setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Portfolio Analysis</h2>
        <p className="text-gray-600">Analyze your portfolio allocation, diversification, and risk</p>
      </div>

      {/* Portfolio Summary */}
      {holdings.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <p className="text-sm text-blue-600 font-medium">Holdings</p>
            <p className="text-2xl font-bold text-blue-900">{holdings.length}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <p className="text-sm text-green-600 font-medium">Total Value</p>
            <p className="text-2xl font-bold text-green-900">
              ${holdings.reduce((sum, h) => sum + (h.quantity * h.currentPrice), 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <p className="text-sm text-purple-600 font-medium">Avg Price</p>
            <p className="text-2xl font-bold text-purple-900">
              ${(holdings.reduce((sum, h) => sum + h.currentPrice, 0) / holdings.length).toFixed(2)}
            </p>
          </div>
          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
            <p className="text-sm text-orange-600 font-medium">Tickers</p>
            <p className="text-2xl font-bold text-orange-900">
              {holdings.map(h => h.ticker).join(', ')}
            </p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Analysis Buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => handleAnalyze('allocation')}
          disabled={loading || holdings.length === 0}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Analyzing...' : 'Allocation'}
        </button>
        <button
          onClick={() => handleAnalyze('diversification')}
          disabled={loading || holdings.length === 0}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Analyzing...' : 'Diversification'}
        </button>
        <button
          onClick={() => handleAnalyze('rebalance')}
          disabled={loading || holdings.length === 0}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Analyzing...' : 'Rebalance'}
        </button>
        <button
          onClick={() => handleAnalyze('full')}
          disabled={loading || holdings.length === 0}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Analyzing...' : 'Full Analysis'}
        </button>
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-xl font-bold text-gray-900">Analysis Results</h3>
          
          {/* Main message */}
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
            {analysis.message}
          </div>

          {/* Structured data if available */}
          {analysis.structured_data && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">📊 Detailed Metrics</h4>
              
              {/* Key metrics summary */}
              {analysis.structured_data.total_portfolio_value && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                  <div className="bg-white p-3 rounded border border-blue-100">
                    <p className="text-xs text-gray-600 font-semibold uppercase">Portfolio Value</p>
                    <p className="text-xl font-bold text-blue-600">${parseFloat(analysis.structured_data.total_portfolio_value).toLocaleString('en-US', { maximumFractionDigits: 0 })}</p>
                  </div>
                  {analysis.structured_data.diversification_score && (
                    <div className="bg-white p-3 rounded border border-green-100">
                      <p className="text-xs text-gray-600 font-semibold uppercase">Diversification</p>
                      <p className="text-xl font-bold text-green-600">{parseFloat(analysis.structured_data.diversification_score).toFixed(1)}/100</p>
                    </div>
                  )}
                  {analysis.structured_data.risk_level && (
                    <div className="bg-white p-3 rounded border border-orange-100">
                      <p className="text-xs text-gray-600 font-semibold uppercase">Risk Level</p>
                      <p className="text-xl font-bold text-orange-600">{analysis.structured_data.risk_level.toUpperCase()}</p>
                    </div>
                  )}
                  {analysis.structured_data.holdings_count && (
                    <div className="bg-white p-3 rounded border border-purple-100">
                      <p className="text-xs text-gray-600 font-semibold uppercase">Holdings</p>
                      <p className="text-xl font-bold text-purple-600">{analysis.structured_data.holdings_count}</p>
                    </div>
                  )}
                  {analysis.structured_data.allocation && (
                    <div className="bg-white p-3 rounded border border-pink-100 md:col-span-2">
                      <p className="text-xs text-gray-600 font-semibold uppercase mb-2">Top Holdings</p>
                      <div className="space-y-1">
                        {analysis.structured_data.allocation.slice(0, 3).map((item: any, idx: number) => (
                          <div key={idx} className="flex justify-between text-xs">
                            <span className="font-medium">{item.ticker}</span>
                            <span className="text-gray-600">{parseFloat(item.allocation_pct).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Collapsible JSON view */}
              <details className="cursor-pointer">
                <summary className="font-medium text-gray-700 hover:text-gray-900 bg-gray-50 p-3 rounded border border-gray-200">
                  📋 View all calculations (JSON)
                </summary>
                <div className="mt-3 bg-gray-900 text-gray-100 rounded border border-gray-700 overflow-hidden">
                  <pre className="text-xs p-4 overflow-x-auto max-h-96 overflow-y-auto font-mono leading-relaxed">
                    {JSON.stringify(analysis.structured_data, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}

          {/* Citations */}
          {analysis.citations && analysis.citations.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-3">📚 Sources</h4>
              <ul className="space-y-2">
                {analysis.citations.map((citation: any, idx: number) => (
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
      {!analysis && holdings.length > 0 && !loading && (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">Click a button above to analyze your portfolio</p>
        </div>
      )}
    </div>
  );
}
