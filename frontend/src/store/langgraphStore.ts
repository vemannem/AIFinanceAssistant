import create from 'zustand'
import { ExecutionMetrics } from '../types'

interface LangGraphExecution extends ExecutionMetrics {
  timestamp: Date
  message?: string
}

interface LangGraphStore {
  lastExecution: LangGraphExecution | null
  loading: boolean

  // Actions
  setExecution: (execution: LangGraphExecution) => void
  setLoading: (loading: boolean) => void
  clearExecution: () => void
  getLastExecution: () => LangGraphExecution | null
}

export const useLangGraphStore = create<LangGraphStore>((set, get) => ({
  lastExecution: null,
  loading: false,

  setExecution: (execution: LangGraphExecution) =>
    set({
      lastExecution: {
        ...execution,
        timestamp: execution.timestamp || new Date(),
      },
    }),

  setLoading: (loading: boolean) => set({ loading }),

  clearExecution: () =>
    set({
      lastExecution: null,
    }),

  getLastExecution: () => get().lastExecution,
}))
