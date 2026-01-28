import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Zap, Clock, AlertCircle, CheckCircle } from 'lucide-react';

interface ExecutionTimeDetail {
  [key: string]: number;
}

interface ExecutionMetadata {
  agents_used?: string[];
  intent?: string;
  execution_summary?: {
    total_agents: number;
    errors: number;
  };
  [key: string]: any;
}

interface ExecutionDetailsProps {
  confidence?: number;
  intent?: string;
  agentsUsed?: string[];
  executionTimes?: ExecutionTimeDetail;
  totalTimeMs?: number;
  metadata?: ExecutionMetadata;
}

const ExecutionDetails: React.FC<ExecutionDetailsProps> = ({
  confidence = 0,
  intent = 'unknown',
  agentsUsed = [],
  executionTimes = {},
  totalTimeMs = 0,
  metadata = {}
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!confidence && !agentsUsed.length && !totalTimeMs) {
    return null;
  }
  // Check if we have execution details in metadata
  const hasExecutionDetails = metadata?.execution_details && Array.isArray(metadata.execution_details) && metadata.execution_details.length > 0
  const hasWorkflowAnalysis = metadata?.workflow_analysis && Object.keys(metadata.workflow_analysis).length > 0
  const formatTime = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getConfidenceColor = (conf: number): string => {
    if (conf >= 0.8) return 'bg-green-100 text-green-800 border-green-300';
    if (conf >= 0.6) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  const getIntentBadgeColor = (intentName: string): string => {
    const colors: { [key: string]: string } = {
      education_question: 'bg-blue-100 text-blue-800 border-blue-300',
      portfolio_analysis: 'bg-purple-100 text-purple-800 border-purple-300',
      market_analysis: 'bg-indigo-100 text-indigo-800 border-indigo-300',
      tax_question: 'bg-orange-100 text-orange-800 border-orange-300',
      news_analysis: 'bg-cyan-100 text-cyan-800 border-cyan-300',
      goal_planning: 'bg-pink-100 text-pink-800 border-pink-300',
      investment_plan: 'bg-violet-100 text-violet-800 border-violet-300'
    };
    return colors[intentName] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const totalAgentTime = Object.values(executionTimes).reduce((a, b) => a + b, 0);
  const otherTime = totalTimeMs - totalAgentTime;

  return (
    <div className="mt-3 border border-gray-200 rounded-lg bg-gray-50">
      {/* Header - Always Visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Zap size={18} className="text-blue-600" />
          <span className="font-semibold text-gray-800">Execution Details</span>
          {(hasExecutionDetails || hasWorkflowAnalysis) && (
            <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded">
              Active
            </span>
          )}
          <div className="flex gap-2">
            {confidence > 0 && (
              <span className={`text-xs px-2 py-1 rounded-full border ${getConfidenceColor(confidence)}`}>
                Confidence: {(confidence * 100).toFixed(0)}%
              </span>
            )}
            {intent && intent !== 'unknown' && (
              <span className={`text-xs px-2 py-1 rounded-full border font-medium ${getIntentBadgeColor(intent)}`}>
                {intent.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        </div>
        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 px-4 py-4 bg-white">
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            {/* Total Time */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-3 border border-blue-200">
              <div className="flex items-center gap-2 mb-1">
                <Clock size={16} className="text-blue-600" />
                <span className="text-xs font-semibold text-gray-600">Total Time</span>
              </div>
              <div className="text-lg font-bold text-blue-900">
                {formatTime(totalTimeMs)}
              </div>
            </div>

            {/* Agents Used */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-3 border border-purple-200">
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle size={16} className="text-purple-600" />
                <span className="text-xs font-semibold text-gray-600">Agents</span>
              </div>
              <div className="text-lg font-bold text-purple-900">
                {agentsUsed.length}
              </div>
            </div>

            {/* Confidence */}
            {confidence > 0 && (
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-3 border border-green-200">
                <div className="flex items-center gap-2 mb-1">
                  <Zap size={16} className="text-green-600" />
                  <span className="text-xs font-semibold text-gray-600">Confidence</span>
                </div>
                <div className="text-lg font-bold text-green-900">
                  {(confidence * 100).toFixed(0)}%
                </div>
              </div>
            )}

            {/* Intent */}
            {intent && intent !== 'unknown' && (
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-3 border border-orange-200">
                <div className="flex items-center gap-2 mb-1">
                  <AlertCircle size={16} className="text-orange-600" />
                  <span className="text-xs font-semibold text-gray-600">Intent</span>
                </div>
                <div className="text-sm font-bold text-orange-900 truncate">
                  {intent.replace(/_/g, ' ')}
                </div>
              </div>
            )}
          </div>

          {/* Agents List */}
          {agentsUsed.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Agents Executed</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {agentsUsed.map((agent, idx) => (
                  <div
                    key={idx}
                    className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-3 border border-indigo-200 flex items-center gap-2"
                  >
                    <CheckCircle size={16} className="text-green-600 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate capitalize">
                        {agent.replace(/_/g, ' ')}
                      </p>
                      {executionTimes[agent] && (
                        <p className="text-xs text-gray-600">
                          {formatTime(executionTimes[agent])}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Execution Details from LangGraph State */}
          {metadata?.execution_details && Array.isArray(metadata.execution_details) && metadata.execution_details.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Agent Execution Report</h4>
              <div className="space-y-2">
                {metadata.execution_details.map((detail: any, idx: number) => (
                  <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {detail.status === 'success' ? (
                        <CheckCircle size={16} className="text-green-600" />
                      ) : (
                        <AlertCircle size={16} className="text-red-600" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-gray-800 capitalize">
                          {detail.agent_name?.replace(/_/g, ' ')}
                        </p>
                        {detail.error && (
                          <p className="text-xs text-red-600">{detail.error}</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-mono text-gray-600">
                        {formatTime(detail.execution_time_ms)}
                      </p>
                      <p className="text-xs text-gray-500 capitalize">
                        {detail.status}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Workflow Analysis */}
          {metadata?.workflow_analysis && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Workflow Analysis</h4>
              <div className="space-y-2 bg-gray-100 rounded-lg p-3">
                {metadata.workflow_analysis.detected_intents && metadata.workflow_analysis.detected_intents.length > 0 && (
                  <div className="text-xs">
                    <span className="font-semibold text-gray-700">Detected Intents: </span>
                    <span className="text-gray-600">{metadata.workflow_analysis.detected_intents.join(', ')}</span>
                  </div>
                )}
                {metadata.workflow_analysis.extracted_tickers && metadata.workflow_analysis.extracted_tickers.length > 0 && (
                  <div className="text-xs">
                    <span className="font-semibold text-gray-700">Tickers: </span>
                    <span className="text-gray-600">{metadata.workflow_analysis.extracted_tickers.join(', ')}</span>
                  </div>
                )}
                {metadata.workflow_analysis.execution_errors && metadata.workflow_analysis.execution_errors.length > 0 && (
                  <div className="text-xs">
                    <span className="font-semibold text-red-700">Errors: </span>
                    <span className="text-red-600">{metadata.workflow_analysis.execution_errors.join(', ')}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Execution Timeline */}
          {Object.keys(executionTimes).length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Execution Timeline</h4>
              <div className="space-y-2 bg-gray-100 rounded-lg p-3">
                {/* Preparation Phase */}
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">
                    ├─ Input Processing & Intent Detection
                  </span>
                  <span className="font-mono text-gray-700 font-semibold">
                    {formatTime(otherTime / 2)}
                  </span>
                </div>

                {/* Agent Execution */}
                {Object.entries(executionTimes).map(([agent, time], idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs">
                    <span className="text-gray-600">
                      ├─ {agent.replace(/_/g, ' ')}
                    </span>
                    <span className="font-mono text-gray-700 font-semibold">
                      {formatTime(time)}
                    </span>
                  </div>
                ))}

                {/* Synthesis Phase */}
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">
                    └─ Response Synthesis & Formatting
                  </span>
                  <span className="font-mono text-gray-700 font-semibold">
                    {formatTime(otherTime / 2)}
                  </span>
                </div>

                {/* Total */}
                <div className="border-t border-gray-300 pt-2 mt-2 flex items-center justify-between text-xs font-bold">
                  <span className="text-gray-800">Total Execution Time</span>
                  <span className="text-blue-700 font-mono">
                    {formatTime(totalTimeMs)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          {totalTimeMs > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Performance</h4>
              <div className="space-y-2">
                {/* Overall Performance */}
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">Response Latency</span>
                  <span className={`font-semibold ${
                    totalTimeMs < 2000 ? 'text-green-700' :
                    totalTimeMs < 4000 ? 'text-yellow-700' :
                    'text-red-700'
                  }`}>
                    {formatTime(totalTimeMs)}
                    <span className="text-gray-500 text-xs ml-1">
                      {totalTimeMs < 2000 ? '(Excellent)' :
                       totalTimeMs < 4000 ? '(Good)' :
                       '(Slow)'}
                    </span>
                  </span>
                </div>

                {/* Parallel Efficiency */}
                {agentsUsed.length > 1 && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-600">Parallel Efficiency</span>
                    <span className="font-semibold text-blue-700">
                      {agentsUsed.length}x agents (concurrent)
                    </span>
                  </div>
                )}

                {/* Confidence Level */}
                {confidence > 0 && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-600">Response Confidence</span>
                    <div className="w-20 h-2 bg-gray-300 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          confidence >= 0.8 ? 'bg-green-500' :
                          confidence >= 0.6 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${confidence * 100}%` }}
                      />
                    </div>
                    <span className="font-semibold text-gray-700 ml-2">
                      {(confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Additional Metadata */}
          {metadata && Object.keys(metadata).length > 0 && (
            <div className="bg-gray-100 rounded-lg p-3 text-xs">
              <details className="cursor-pointer">
                <summary className="font-semibold text-gray-700 select-none">
                  Additional Metadata
                </summary>
                <pre className="mt-2 overflow-auto text-gray-700 bg-white p-2 rounded border border-gray-300">
                  {JSON.stringify(metadata, null, 2)}
                </pre>
              </details>
            </div>
          )}

          {/* Footer Info */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              💡 This execution details view is powered by LangGraph StateGraph for transparent workflow execution tracking.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionDetails;
