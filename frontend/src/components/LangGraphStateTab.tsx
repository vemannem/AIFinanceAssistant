import React, { useState } from 'react';
import { Zap, ChevronDown, ChevronUp, Clock, CheckCircle, AlertCircle, BarChart3 } from 'lucide-react';
import { useLangGraphStore } from '../store/langgraphStore';
import { Message, ExecutionMetrics } from '../types';

interface LangGraphStateTabProps {
  messages: Message[];
  loading: boolean;
}

const LangGraphStateTab: React.FC<LangGraphStateTabProps> = ({ loading }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);
  const langgraphStore = useLangGraphStore();

  // Get execution from LangGraph store (independent of chat messages)
  const lastExecution = langgraphStore.lastExecution;
  const storeLoading = langgraphStore.loading;
  
  // Show loading if either the passed loading prop or store loading is true
  const isLoading = loading || storeLoading;
  
  const execution = lastExecution ? {
    confidence: lastExecution.confidence,
    intent: lastExecution.intent,
    agentsUsed: lastExecution.agentsUsed,
    executionTimes: lastExecution.executionTimes,
    totalTimeMs: lastExecution.totalTimeMs,
  } as ExecutionMetrics : undefined;

  // Show loading state with progress indicator
  if (isLoading && !execution) {
    return (
      <div className="flex items-center justify-center h-full text-center py-12">
        <div className="text-center space-y-4">
          <div className="animate-spin inline-block w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full"></div>
          <p className="text-gray-700 font-semibold">Processing your request...</p>
          <p className="text-sm text-gray-500">LangGraph is executing agents and collecting metrics</p>
          
          {/* Simulated progress */}
          <div className="mt-6 w-64 mx-auto">
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse rounded-full" style={{ width: '60%' }}></div>
            </div>
            <p className="text-xs text-gray-500 mt-2">This may take 10-30 seconds...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show no data when not loading and no execution
  if (!execution) {
    return (
      <div className="flex items-center justify-center h-full text-center py-12">
        <div className="text-gray-500">
          <Zap size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-semibold mb-2">No Execution Data</p>
          <p className="text-sm">Run a goal planning, market analysis, or other agent to see execution details</p>
        </div>
      </div>
    );
  }

  const formatTime = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getConfidenceColor = (conf: number): string => {
    if (conf >= 0.8) return 'bg-green-50 border-green-200 text-green-900';
    if (conf >= 0.6) return 'bg-yellow-50 border-yellow-200 text-yellow-900';
    return 'bg-red-50 border-red-200 text-red-900';
  };

  const getIntentColor = (intentName: string): string => {
    const colors: { [key: string]: string } = {
      education_question: 'bg-blue-50 border-blue-200 text-blue-900',
      portfolio_analysis: 'bg-purple-50 border-purple-200 text-purple-900',
      market_analysis: 'bg-indigo-50 border-indigo-200 text-indigo-900',
      tax_question: 'bg-orange-50 border-orange-200 text-orange-900',
      news_analysis: 'bg-cyan-50 border-cyan-200 text-cyan-900',
      goal_planning: 'bg-pink-50 border-pink-200 text-pink-900',
      investment_plan: 'bg-violet-50 border-violet-200 text-violet-900'
    };
    return colors[intentName] || 'bg-gray-50 border-gray-200 text-gray-900';
  };

  const totalAgentTime = Object.values(execution?.executionTimes || {}).reduce((a, b) => a + b, 0);
  const otherTime = (execution?.totalTimeMs || 0) - totalAgentTime;

  return (
    <div className="flex flex-col h-full bg-gray-50 overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm flex items-center gap-3">
        <Zap size={24} className="text-blue-600" />
        <h2 className="text-xl font-bold text-gray-900">LangGraph Execution State</h2>
        {loading && <span className="ml-auto text-xs text-gray-500">Processing...</span>}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin inline-block w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full mb-4"></div>
              <p className="text-gray-600">Processing message...</p>
            </div>
          </div>
        ) : !execution ? (
          <div className="text-center text-gray-500 py-12">
            <p>No execution data available</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Total Time */}
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                <div className="flex items-center gap-2 mb-2">
                  <Clock size={18} className="text-blue-600" />
                  <span className="text-xs font-semibold text-gray-600">Total Execution</span>
                </div>
                <div className="text-2xl font-bold text-blue-900">
                  {formatTime(execution.totalTimeMs || 0)}
                </div>
              </div>

              {/* Agents */}
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle size={18} className="text-purple-600" />
                  <span className="text-xs font-semibold text-gray-600">Agents Executed</span>
                </div>
                <div className="text-2xl font-bold text-purple-900">
                  {execution.agentsUsed?.length || 0}
                </div>
              </div>

              {/* Confidence */}
              {execution.confidence !== undefined && (
                <div className={`rounded-lg p-4 border ${getConfidenceColor(execution.confidence)}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <BarChart3 size={18} />
                    <span className="text-xs font-semibold">Confidence</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {(execution.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              )}

              {/* Intent */}
              {execution.intent && execution.intent !== 'unknown' && (
                <div className={`rounded-lg p-4 border ${getIntentColor(execution.intent)}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle size={18} />
                    <span className="text-xs font-semibold">Detected Intent</span>
                  </div>
                  <div className="text-sm font-bold truncate">
                    {execution.intent.replace(/_/g, ' ')}
                  </div>
                </div>
              )}
            </div>

            {/* Agents Breakdown */}
            {execution.agentsUsed && execution.agentsUsed.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <button
                  onClick={() => setExpandedIndex(expandedIndex === 1 ? null : 1)}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <CheckCircle size={20} className="text-green-600" />
                    <h3 className="font-semibold text-gray-900">Agents Executed</h3>
                    <span className="ml-2 inline-block bg-green-100 text-green-800 text-xs font-bold px-2.5 py-0.5 rounded-full">
                      {execution.agentsUsed.length}
                    </span>
                  </div>
                  {expandedIndex === 1 ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>

                {expandedIndex === 1 && (
                  <div className="border-t border-gray-200 px-6 py-4">
                    <div className="space-y-3">
                      {execution.agentsUsed.map((agent, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-3 border border-green-200"
                        >
                          <div className="flex items-center gap-3">
                            <CheckCircle size={16} className="text-green-600 flex-shrink-0" />
                            <span className="font-medium text-gray-900 capitalize">
                              {agent.replace(/_/g, ' ')}
                            </span>
                          </div>
                          {execution.executionTimes && execution.executionTimes[agent] && (
                            <span className="text-xs font-mono bg-white px-3 py-1 rounded border border-green-200 text-green-900 font-semibold">
                              {formatTime(execution.executionTimes[agent])}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Execution Timeline */}
            {execution.executionTimes && Object.keys(execution.executionTimes).length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <button
                  onClick={() => setExpandedIndex(expandedIndex === 2 ? null : 2)}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Clock size={20} className="text-orange-600" />
                    <h3 className="font-semibold text-gray-900">Execution Timeline</h3>
                  </div>
                  {expandedIndex === 2 ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>

                {expandedIndex === 2 && (
                  <div className="border-t border-gray-200 px-6 py-4">
                    <div className="space-y-2 bg-gray-100 rounded-lg p-4 font-mono text-sm">
                      {/* Input & Intent Detection */}
                      <div className="flex items-center justify-between text-xs text-gray-700">
                        <span>├─ Input Processing & Intent Detection</span>
                        <span className="font-semibold">{formatTime(otherTime / 2)}</span>
                      </div>

                      {/* Agents */}
                      {Object.entries(execution.executionTimes).map(([agent, time], idx, arr) => (
                        <div key={idx} className="flex items-center justify-between text-xs text-gray-700">
                          <span>{idx === arr.length - 1 ? '├─' : '├─'} {agent.replace(/_/g, ' ')}</span>
                          <span className="font-semibold text-blue-900">{formatTime(time)}</span>
                        </div>
                      ))}

                      {/* Synthesis */}
                      <div className="flex items-center justify-between text-xs text-gray-700">
                        <span>└─ Response Synthesis & Formatting</span>
                        <span className="font-semibold">{formatTime(otherTime / 2)}</span>
                      </div>

                      {/* Total */}
                      <div className="border-t border-gray-300 pt-2 mt-2 flex items-center justify-between text-xs font-bold text-gray-900">
                        <span>Total Execution Time</span>
                        <span className="text-blue-700">{formatTime(execution.totalTimeMs || 0)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Performance Analysis */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <button
                onClick={() => setExpandedIndex(expandedIndex === 3 ? null : 3)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <BarChart3 size={20} className="text-indigo-600" />
                  <h3 className="font-semibold text-gray-900">Performance Analysis</h3>
                </div>
                {expandedIndex === 3 ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </button>

              {expandedIndex === 3 && (
                <div className="border-t border-gray-200 px-6 py-4">
                  <div className="space-y-4">
                    {/* Response Latency */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Response Latency</span>
                        <span className={`text-sm font-semibold ${
                          (execution.totalTimeMs || 0) < 2000 ? 'text-green-700' :
                          (execution.totalTimeMs || 0) < 4000 ? 'text-yellow-700' :
                          'text-red-700'
                        }`}>
                          {formatTime(execution.totalTimeMs || 0)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {(execution.totalTimeMs || 0) < 2000 ? '✅ Excellent' :
                         (execution.totalTimeMs || 0) < 4000 ? '⚠️ Good' :
                         '🔴 Slow'}
                      </div>
                    </div>

                    {/* Parallel Efficiency */}
                    {execution.agentsUsed && execution.agentsUsed.length > 1 && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">Parallel Efficiency</span>
                          <span className="text-sm font-semibold text-blue-700">
                            {execution.agentsUsed.length}x agents (concurrent)
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          Multiple agents executed in parallel for faster response
                        </div>
                      </div>
                    )}

                    {/* Confidence */}
                    {execution.confidence !== undefined && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">Response Confidence</span>
                          <span className="text-sm font-semibold">
                            {(execution.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              execution.confidence >= 0.8 ? 'bg-green-500' :
                              execution.confidence >= 0.6 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${execution.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Metadata */}
            {execution.metadata && Object.keys(execution.metadata).length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <button
                  onClick={() => setExpandedIndex(expandedIndex === 4 ? null : 4)}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <h3 className="font-semibold text-gray-900">Additional Metadata</h3>
                  {expandedIndex === 4 ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>

                {expandedIndex === 4 && (
                  <div className="border-t border-gray-200 px-6 py-4">
                    <pre className="bg-gray-100 p-4 rounded text-xs overflow-auto max-h-64 text-gray-700">
                      {JSON.stringify(execution.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Footer */}
            <div className="text-xs text-gray-500 text-center py-4 border-t border-gray-200 mt-4">
              <p>💡 LangGraph StateGraph provides transparent workflow execution tracking</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LangGraphStateTab;
