import { FC, useState } from 'react'
import { Message } from '../../types'
import { formatTime, copyToClipboard } from '@utils/helpers'
import { CitationsList } from './CitationsList'
import { AgentResultDisplay } from '../AgentResultDisplay'
import ExecutionDetails from './ExecutionDetails'

interface MessageBubbleProps {
  message: Message
  onDelete?: (id: string) => void
}

/**
 * MessageBubble Component
 * Displays individual chat messages with styling based on sender
 */
export const MessageBubble: FC<MessageBubbleProps> = ({
  message,
  onDelete,
}) => {
  const isUser = message.sender === 'user'
  const [showAgentDetails, setShowAgentDetails] = useState(false)

  const handleCopy = async () => {
    const success = await copyToClipboard(message.text)
    if (success) {
      // TODO: Show toast notification
      console.log('Copied to clipboard')
    }
  }

  // Debug logging
  if (!isUser && message.execution) {
    console.log('MessageBubble rendering with execution data:', message.execution)
  }

  return (
    <div
      className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'} gap-2`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${
          isUser ? 'bg-blue-600 order-2' : 'bg-gray-400'
        }`}
      >
        {isUser ? 'You' : 'AI'}
      </div>

      {/* Message Content */}
      <div
        className={`max-w-lg lg:max-w-2xl ${isUser ? 'order-1' : 'order-3'}`}
      >
        <div
          className={`px-4 py-3 rounded-lg ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-none'
              : 'bg-gray-100 text-gray-900 rounded-bl-none'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.text}
          </p>

          {/* Timestamp and Actions */}
          <div
            className={`flex items-center justify-between mt-2 pt-2 border-t ${
              isUser ? 'border-blue-500' : 'border-gray-200'
            }`}
          >
            <span
              className={`text-xs ${
                isUser ? 'text-blue-200' : 'text-gray-500'
              }`}
            >
              {formatTime(message.timestamp)}
            </span>

            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className={`text-xs px-2 py-1 rounded hover:opacity-80 transition-opacity ${
                  isUser
                    ? 'hover:bg-blue-500'
                    : 'hover:bg-gray-200 text-gray-600'
                }`}
                title="Copy message"
              >
                Copy
              </button>
              {onDelete && !isUser && (
                <button
                  onClick={() => onDelete(message.id)}
                  className="text-xs px-2 py-1 rounded text-gray-600 hover:bg-gray-200 hover:text-red-600 transition-colors"
                  title="Delete message"
                >
                  Delete
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2">
            <CitationsList citations={message.citations} />
          </div>
        )}

        {/* Execution Details - LangGraph State */}
        {!isUser && message.execution && (
          <div className="mt-2">
            <ExecutionDetails
              confidence={message.execution.confidence}
              intent={message.execution.intent}
              agentsUsed={message.execution.agentsUsed}
              executionTimes={message.execution.executionTimes}
              totalTimeMs={message.execution.totalTimeMs}
              metadata={message.execution.metadata}
            />
          </div>
        )}

        {/* Agent Results */}
        {message.agentResults && message.agentResults.length > 0 && !isUser && (
          <div className="mt-3">
            <button
              onClick={() => setShowAgentDetails(!showAgentDetails)}
              className="text-xs font-medium text-gray-600 hover:text-gray-900 flex items-center gap-1 p-2 rounded hover:bg-gray-200 transition-colors"
            >
              {showAgentDetails ? '▼' : '▶'} 
              {message.agentResults.length} Agent Result{message.agentResults.length !== 1 ? 's' : ''}
            </button>
            {showAgentDetails && (
              <div className="mt-2 space-y-2">
                {message.agentResults.map((result, idx) => (
                  <AgentResultDisplay key={idx} result={result} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
