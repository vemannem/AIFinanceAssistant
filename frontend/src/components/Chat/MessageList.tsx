import { FC, useEffect, useRef } from 'react'
import { Message } from '../../types'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'

interface MessageListProps {
  messages: Message[]
  loading?: boolean
  onDeleteMessage?: (id: string) => void
}

/**
 * MessageList Component
 * Displays conversation history with auto-scroll to latest message
 */
export const MessageList: FC<MessageListProps> = ({
  messages,
  loading = false,
  onDeleteMessage,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
      {/* Empty state */}
      {messages.length === 0 && !loading && (
        <div className="flex items-center justify-center h-full text-center">
          <div className="text-gray-500">
            <p className="text-lg font-semibold mb-2">
              Start a conversation
            </p>
            <p className="text-sm">
              Ask me anything about your finances or portfolio
            </p>
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onDelete={onDeleteMessage}
        />
      ))}

      {/* Loading indicator */}
      {loading && <TypingIndicator text="AI is analyzing..." />}

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}

export default MessageList
