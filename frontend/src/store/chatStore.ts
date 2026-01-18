import create from 'zustand'
import { Message, ConversationSummary } from '../types'

interface ChatStore {
  messages: Message[]
  loading: boolean
  error: string | null
  sessionId: string
  summary: ConversationSummary | null

  // Actions
  addMessage: (message: Message) => void
  removeMessage: (id: string) => void
  clearMessages: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setSessionId: (id: string) => void
  setSummary: (summary: ConversationSummary | null) => void
  getMessageCount: () => number
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  loading: false,
  error: null,
  sessionId: '',
  summary: null,

  addMessage: (message: Message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  removeMessage: (id: string) =>
    set((state) => ({
      messages: state.messages.filter((msg) => msg.id !== id),
    })),

  clearMessages: () =>
    set({
      messages: [],
      summary: null,
      error: null,
    }),

  setLoading: (loading: boolean) => set({ loading }),

  setError: (error: string | null) => set({ error }),

  setSessionId: (id: string) => set({ sessionId: id }),

  setSummary: (summary: ConversationSummary | null) => set({ summary }),

  getMessageCount: () => get().messages.length,
}))
