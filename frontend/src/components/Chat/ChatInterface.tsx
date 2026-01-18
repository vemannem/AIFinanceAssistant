import { FC, useEffect } from 'react'
import { useChat } from '../../hooks/useChat'
import MessageList from './MessageList'
import InputBox from './InputBox'
import ExecutionDetails from './ExecutionDetails'

interface ChatInterfaceProps {
  title?: string
  showHeader?: boolean
}

/**
 * ChatInterface Component
 * Main chat container integrating all chat sub-components
 * Manages message flow and API integration
 */
export const ChatInterface: FC<ChatInterfaceProps> = ({
  title = 'AI Finance Assistant',
  showHeader = true,
}) => {
  const { messages, loading, error, sessionId, sendMessage, clearChat } =
    useChat()

  // Log session ID on mount
  useEffect(() => {
    console.log('Chat session ID:', sessionId)
  }, [sessionId])

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      {showHeader && (
        <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
              <p className="text-sm text-gray-600 mt-1">
                Session ID: {sessionId || 'Loading...'}
              </p>
            </div>

            {/* Clear button */}
            {messages.length > 0 && (
              <button
                onClick={() => {
                  if (
                    window.confirm(
                      'Are you sure you want to clear the conversation?'
                    )
                  ) {
                    clearChat()
                  }
                }}
                className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                Clear Chat
              </button>
            )}
          </div>
        </header>
      )}

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3">
          <p className="text-sm text-red-800">
            <span className="font-semibold">Error: </span>
            {error}
          </p>
        </div>
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Message list */}
        <MessageList messages={messages} loading={loading} />

        {/* Input box */}
        <InputBox onSubmit={sendMessage} loading={loading} disabled={!!error} />
      </div>
    </div>
  )
}

export default ChatInterface
