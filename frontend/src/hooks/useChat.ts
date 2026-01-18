import { useCallback, useState } from 'react'
import { useChatStore } from '../store/chatStore'
import { orchestrationService } from '../services/orchestrationService'
import { Message } from '../types'
import { generateSessionId, generateMessageId } from '../utils/helpers'

interface UseChat {
  messages: Message[]
  loading: boolean
  error: string | null
  sessionId: string
  sendMessage: (text: string) => Promise<void>
  clearChat: () => void
  deleteMessage: (id: string) => void
}

export const useChat = (): UseChat => {
  const store = useChatStore()
  const [localError, setLocalError] = useState<string | null>(null)

  // Initialize session ID if needed
  const ensureSessionId = useCallback(() => {
    if (!store.sessionId) {
      const newId = generateSessionId()
      store.setSessionId(newId)
      localStorage.setItem('sessionId', newId)
    }
  }, [store])

  // Send message to backend via orchestration
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) {
        setLocalError('Message cannot be empty')
        return
      }

      try {
        setLocalError(null)
        ensureSessionId()

        // Add user message immediately
        const userMessage: Message = {
          id: generateMessageId(),
          text,
          sender: 'user',
          timestamp: new Date(),
        }
        store.addMessage(userMessage)
        store.setLoading(true)

        // Call backend orchestration API
        const response = await orchestrationService.sendMessage(
          text,
          store.sessionId,
          store.messages.map(msg => ({
            role: msg.sender as 'user' | 'assistant',
            content: msg.text,
          }))
        )

        // Create assistant message from response
        let assistantText = response.message

        // Add agent and tools info to message
        assistantText += `\n\n*Agent: ${response.metadata.agent} | Tools: ${response.metadata.tools_used.join(', ')}*`

        // Add assistant response
        const executionData = {
          confidence: response.confidence || 0.8,
          intent: response.intent,
          agentsUsed: response.agents_used || [],
          executionTimes: response.execution_times || {},
          totalTimeMs: response.total_time_ms || 0,
          metadata: response.metadata,
        }
        console.log('ExecutionData being set:', executionData)
        
        const assistantMessage: Message = {
          id: generateMessageId(),
          text: assistantText,
          sender: 'assistant',
          timestamp: new Date(),
          citations: response.citations?.map((c, i) => ({
            id: `citation-${i}`,
            title: c.title,
            url: c.source_url,
            source: c.source_url,
          })),
          execution: executionData,
          metadata: {
            workflow_state: 'complete',
            confidence_score: response.confidence || 0.9,
            agents_count: response.agents_used?.length || 1,
            error_messages: [],
          },
        }
        store.addMessage(assistantMessage)
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : 'Failed to send message'
        setLocalError(errorMsg)
        store.setError(errorMsg)
      } finally {
        store.setLoading(false)
      }
    },
    [store, ensureSessionId]
  )

  return {
    messages: store.messages,
    loading: store.loading,
    error: localError || store.error,
    sessionId: store.sessionId,
    sendMessage,
    clearChat: store.clearMessages,
    deleteMessage: store.removeMessage,
  }
}
