import { FC, useState, useEffect } from 'react'
import { useChatStore } from '../../store/chatStore'

interface Conversation {
  sessionId: string
  summary: string
  messageCount: number
  timestamp: string
  tags: string[]
}

/**
 * ConversationHistory Component
 * Displays previous conversations with search and filter
 */
export const ConversationHistory: FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const store = useChatStore()

  // Load conversations from localStorage on mount
  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = () => {
    setIsLoading(true)
    try {
      // Simulate API call - in production, call /api/chat/history
      const savedConversations = localStorage.getItem('conversations')
      const parsed = savedConversations ? JSON.parse(savedConversations) : []
      setConversations(parsed)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Save conversation when messages change
  useEffect(() => {
    if (store.messages.length > 0) {
      saveCurrentConversation()
    }
  }, [store.messages, store.sessionId])

  const saveCurrentConversation = () => {
    const summary = generateSummary()
    const newConversation: Conversation = {
      sessionId: store.sessionId,
      summary,
      messageCount: store.messages.length,
      timestamp: new Date().toISOString(),
      tags: extractTags(summary),
    }

    const existing = conversations.filter((c) => c.sessionId !== store.sessionId)
    const updated = [newConversation, ...existing]
    setConversations(updated)
    localStorage.setItem('conversations', JSON.stringify(updated))
  }

  const generateSummary = (): string => {
    if (store.messages.length === 0) return 'Empty conversation'
    const firstUserMsg = store.messages.find((m) => m.sender === 'user')?.text || ''
    return firstUserMsg.substring(0, 100) + (firstUserMsg.length > 100 ? '...' : '')
  }

  const extractTags = (summary: string): string[] => {
    const keywords = ['portfolio', 'market', 'investing', 'dividend', 'etf', 'stock', 'goal', 'tax']
    const tags: string[] = []
    keywords.forEach((keyword) => {
      if (summary.toLowerCase().includes(keyword)) {
        tags.push(keyword)
      }
    })
    return tags.slice(0, 3) // Limit to 3 tags
  }

  const filteredConversations = conversations.filter(
    (conv) =>
      conv.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conv.tags.some((tag) => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const deleteConversation = (sessionId: string) => {
    const updated = conversations.filter((c) => c.sessionId !== sessionId)
    setConversations(updated)
    localStorage.setItem('conversations', JSON.stringify(updated))
  }

  const loadConversation = (sessionId: string) => {
    // In production: fetch messages from backend and restore to store
    console.log('Loading conversation:', sessionId)
    // store.setMessages(...)
  }

  const formatDate = (timestamp: string): string => {
    const date = new Date(timestamp)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday'
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Header */}
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Conversation History</h2>
        <p className="text-sm text-gray-600">Access previous conversations</p>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        />
      </div>

      {/* Conversation List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {isLoading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading conversations...</p>
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600">No conversations found</p>
          </div>
        ) : (
          filteredConversations.map((conv) => (
            <div key={conv.sessionId} className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
              {/* Conversation Item Header */}
              <div
                onClick={() => setExpandedId(expandedId === conv.sessionId ? null : conv.sessionId)}
                className="cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{conv.summary}</p>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-gray-500">{formatDate(conv.timestamp)}</span>
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {conv.messageCount} messages
                      </span>
                    </div>
                  </div>
                  <span className="ml-2 text-gray-400">
                    {expandedId === conv.sessionId ? '▾' : '▸'}
                  </span>
                </div>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1 mt-2">
                {conv.tags.map((tag) => (
                  <span key={tag} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                    {tag}
                  </span>
                ))}
              </div>

              {/* Expanded Actions */}
              {expandedId === conv.sessionId && (
                <div className="flex gap-2 mt-3 pt-3 border-t border-gray-200">
                  <button
                    onClick={() => loadConversation(conv.sessionId)}
                    className="flex-1 px-3 py-1 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded transition-colors"
                  >
                    Load
                  </button>
                  <button
                    onClick={() => {
                      const text = `Conversation: ${conv.summary}\nMessages: ${conv.messageCount}\nDate: ${formatDate(conv.timestamp)}`
                      navigator.clipboard.writeText(text)
                      alert('Conversation info copied!')
                    }}
                    className="flex-1 px-3 py-1 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded transition-colors"
                  >
                    Copy
                  </button>
                  <button
                    onClick={() => {
                      if (window.confirm('Delete this conversation?')) {
                        deleteConversation(conv.sessionId)
                      }
                    }}
                    className="flex-1 px-3 py-1 text-sm font-medium text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Stats Footer */}
      {conversations.length > 0 && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 text-center">
            {conversations.length} total conversations • {conversations.reduce((sum, c) => sum + c.messageCount, 0)}{' '}
            total messages
          </p>
        </div>
      )}
    </div>
  )
}

export default ConversationHistory
