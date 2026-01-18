import React from 'react';
import { AgentExecutionResult } from '@/services/orchestrationService';

interface AgentResultDisplayProps {
  result: AgentExecutionResult;
}

export function AgentResultDisplay({ result }: AgentResultDisplayProps) {
  const getAgentIcon = (agentName: string): string => {
    const name = agentName.toLowerCase();
    if (name.includes('portfolio')) return '📊';
    if (name.includes('market')) return '📈';
    if (name.includes('goal')) return '🎯';
    if (name.includes('tax')) return '💰';
    if (name.includes('news')) return '📰';
    if (name.includes('finance') || name.includes('qa')) return '❓';
    return '🤖';
  };

  const getAgentColor = (agentName: string): string => {
    const name = agentName.toLowerCase();
    if (name.includes('portfolio')) return 'border-blue-500 bg-blue-50';
    if (name.includes('market')) return 'border-green-500 bg-green-50';
    if (name.includes('goal')) return 'border-purple-500 bg-purple-50';
    if (name.includes('tax')) return 'border-orange-500 bg-orange-50';
    if (name.includes('news')) return 'border-red-500 bg-red-50';
    return 'border-gray-500 bg-gray-50';
  };

  return (
    <div className={`border-l-4 ${getAgentColor(result.agent_name)} p-4 my-3 rounded`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{getAgentIcon(result.agent_name)}</span>
        <h4 className="font-semibold text-gray-800">
          {result.agent_name.replace(/_/g, ' ').toUpperCase()}
        </h4>
      </div>

      <div className="text-sm text-gray-700 mb-3 whitespace-pre-wrap">
        {result.answer_text}
      </div>

      {result.structured_data && (
        <details className="mt-3">
          <summary className="text-xs font-medium text-gray-600 cursor-pointer hover:text-gray-800">
            📋 Structured Data
          </summary>
          <pre className="mt-2 text-xs bg-white border border-gray-300 rounded p-2 overflow-auto max-h-60">
            {JSON.stringify(result.structured_data, null, 2)}
          </pre>
        </details>
      )}

      {result.citations && result.citations.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-300">
          <p className="text-xs font-medium text-gray-600 mb-2">📚 Sources:</p>
          <ul className="space-y-1">
            {result.citations.map((citation, idx) => (
              <li key={idx} className="text-xs">
                <a
                  href={citation.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {citation.title}
                </a>
                {citation.category && (
                  <span className="ml-2 text-gray-500">({citation.category})</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
