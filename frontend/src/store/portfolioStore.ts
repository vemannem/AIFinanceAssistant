import create from 'zustand'
import { Portfolio, Holding } from '../types'

interface PortfolioStore {
  holdings: Holding[]
  totalValue: number
  allocation: Record<string, number>
  diversificationScore: number
  riskScore: number

  // Actions
  addHolding: (holding: Holding) => void
  removeHolding: (ticker: string) => void
  updateHolding: (ticker: string, updates: Partial<Holding>) => void
  clearPortfolio: () => void
  calculateMetrics: () => void
  getPortfolio: () => Portfolio
}

export const usePortfolioStore = create<PortfolioStore>((set, get) => ({
  holdings: [],
  totalValue: 0,
  allocation: {},
  diversificationScore: 0,
  riskScore: 0,

  addHolding: (holding: Holding) =>
    set((state) => {
      const updated = [...state.holdings, holding]
      return { holdings: updated }
    }),

  removeHolding: (ticker: string) =>
    set((state) => ({
      holdings: state.holdings.filter((h) => h.ticker !== ticker),
    })),

  updateHolding: (ticker: string, updates: Partial<Holding>) =>
    set((state) => ({
      holdings: state.holdings.map((h) =>
        h.ticker === ticker ? { ...h, ...updates } : h
      ),
    })),

  clearPortfolio: () =>
    set({
      holdings: [],
      totalValue: 0,
      allocation: {},
      diversificationScore: 0,
      riskScore: 0,
    }),

  calculateMetrics: () => {
    const state = get()
    const total = state.holdings.reduce((sum, h) => sum + (h.value || 0), 0)

    if (total === 0) {
      set({
        totalValue: 0,
        allocation: {},
        diversificationScore: 0,
      })
      return
    }

    const newAllocation: Record<string, number> = {}
    state.holdings.forEach((h) => {
      const percent = ((h.value || 0) / total) * 100
      newAllocation[h.ticker] = percent
    })

    // Calculate diversification (1 - sum of squares of allocations)
    const sumOfSquares = Object.values(newAllocation).reduce(
      (sum, pct) => sum + Math.pow(pct / 100, 2),
      0
    )
    const diversification = Math.max(0, 1 - sumOfSquares)

    set({
      totalValue: total,
      allocation: newAllocation,
      diversificationScore: diversification,
    })
  },

  getPortfolio: (): Portfolio => {
    const state = get()
    return {
      holdings: state.holdings,
      totalValue: state.totalValue,
      allocation: state.allocation,
      diversificationScore: state.diversificationScore,
      riskScore: state.riskScore,
    }
  },
}))
