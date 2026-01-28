import { useState } from 'react';
import { orchestrationService } from '@/services/orchestrationService';
import { useLangGraphStore } from '@/store/langgraphStore';

export function MarketAnalysisView() {
  const langgraphStore = useLangGraphStore();
  const [tickers, setTickers] = useState('AAPL,MSFT,GOOGL');
  const [analysisType, setAnalysisType] = useState('quote');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      setError(null);
      langgraphStore.setLoading(true);

      const tickerList = tickers
        .split(',')
        .map(t => t.trim().toUpperCase())
        .filter(t => t.length > 0);

      if (tickerList.length === 0) {
        setError('Please enter at least one ticker symbol');
        return;
      }

      // Build query string for market analysis
      const analysisTypeText = analysisType === 'quote' ? 'price' : analysisType;
      const query = `Analyze ${tickerList.join(', ')} for ${analysisTypeText} data`;

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
        metadata: result.metadata, // ✅ INCLUDES execution_details and workflow_analysis from LangGraph
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
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Market Analysis</h2>
        <p className="text-gray-600">Get real-time quotes, trends, and fundamentals</p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Ticker Symbols
          </label>
          <input
            type="text"
            value={tickers}
            onChange={(e) => setTickers(e.target.value)}
            placeholder="e.g., AAPL,MSFT,GOOGL"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-1">Separate multiple tickers with commas</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Analysis Type
          </label>
          <select
            value={analysisType}
            onChange={(e) => setAnalysisType(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="quote">Quote (Price & Change)</option>
            <option value="historical">Historical (Trends)</option>
            <option value="fundamentals">Fundamentals (P/E, EPS, etc.)</option>
            <option value="comparison">Comparison (Multi-ticker)</option>
          </select>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {loading ? 'Analyzing...' : 'Analyze Market'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-xl font-bold text-gray-900">Market Analysis Results</h3>
          
          {/* Main message */}
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap max-h-96 overflow-y-auto">
            {analysis.message}
          </div>

          {/* Structured data if available */}
          {analysis.structured_data && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">📊 Market Data</h4>
              
              {/* Quick summary cards */}
              {analysis.structured_data.quotes && Array.isArray(analysis.structured_data.quotes) && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {analysis.structured_data.quotes.slice(0, 6).map((quote: any, idx: number) => (
                    <div key={idx} className="bg-gradient-to-br from-slate-50 to-slate-100 p-4 rounded-lg border border-slate-200">
                      <p className="text-lg font-bold text-slate-900">{quote.ticker}</p>
                      <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
                        <div>
                          <p className="text-xs text-gray-600 font-semibold uppercase">Price</p>
                          <p className="font-bold text-slate-700">${parseFloat(quote.price).toFixed(2)}</p>
                        </div>
                        {quote.change !== undefined && (
                          <div>
                            <p className="text-xs text-gray-600 font-semibold uppercase">Change</p>
                            <p className={`font-bold ${parseFloat(quote.change) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {parseFloat(quote.change) >= 0 ? '+' : ''}{parseFloat(quote.change).toFixed(2)}%
                            </p>
                          </div>
                        )}
                        {quote.dividend_yield && (
                          <div className="col-span-2">
                            <p className="text-xs text-gray-600 font-semibold uppercase">Div Yield</p>
                            <p className="font-bold text-blue-600">{parseFloat(quote.dividend_yield).toFixed(2)}%</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Collapsible JSON view */}
              <details className="cursor-pointer">
                <summary className="font-medium text-gray-700 hover:text-gray-900 bg-gray-50 p-3 rounded border border-gray-200">
                  📋 View all market data (JSON)
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
      {!analysis && !loading && (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">Enter ticker symbols and click analyze to get started</p>
        </div>
      )}
    </div>
  );
}
