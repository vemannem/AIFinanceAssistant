import { FC, useState } from 'react'
import { usePortfolioStore } from '../../store/portfolioStore'

interface Holding {
  id: string
  ticker: string
  shares: number
  pricePerShare: number
  costBasis: number
}

/**
 * PortfolioForm Component
 * Input form for adding/managing portfolio holdings
 * Includes validation and live calculations
 */
export const PortfolioForm: FC = () => {
  const store = usePortfolioStore()
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [ticker, setTicker] = useState('')
  const [shares, setShares] = useState('')
  const [pricePerShare, setPricePerShare] = useState('')
  const [costBasis, setCostBasis] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const generateId = () => `holding-${Date.now()}-${Math.random()}`

  // Validation
  const validateInput = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!ticker.trim()) {
      newErrors.ticker = 'Ticker is required'
    } else if (!ticker.match(/^[A-Z]{1,5}$/)) {
      newErrors.ticker = 'Invalid ticker format (1-5 uppercase letters)'
    }

    const sharesNum = parseFloat(shares)
    if (!shares.trim()) {
      newErrors.shares = 'Shares is required'
    } else if (isNaN(sharesNum) || sharesNum <= 0) {
      newErrors.shares = 'Shares must be > 0'
    }

    const priceNum = parseFloat(pricePerShare)
    if (!pricePerShare.trim()) {
      newErrors.price = 'Price is required'
    } else if (isNaN(priceNum) || priceNum <= 0) {
      newErrors.price = 'Price must be > 0'
    }

    if (shares && pricePerShare) {
      const totalValue = sharesNum * priceNum
      if (totalValue > 10000000) newErrors.total = 'Total value exceeds $10M limit'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Add holding
  const handleAddHolding = () => {
    if (!validateInput()) return

    const newHolding: Holding = {
      id: generateId(),
      ticker: ticker.toUpperCase(),
      shares: parseFloat(shares),
      pricePerShare: parseFloat(pricePerShare),
      costBasis: parseFloat(costBasis || pricePerShare),
    }

    const updated = [...holdings, newHolding]
    setHoldings(updated)
    store.addHolding({
      ticker: newHolding.ticker,
      amount: newHolding.shares * newHolding.pricePerShare,
      quantity: newHolding.shares,
      costBasis: newHolding.costBasis,
    })

    // Reset form
    setTicker('')
    setShares('')
    setPricePerShare('')
    setCostBasis('')
    setPricePerShare('')
    setErrors({})
  }

  // Remove holding
  const handleRemoveHolding = (id: string) => {
    const updated = holdings.filter((h) => h.id !== id)
    setHoldings(updated)
  }

  // Calculate metrics
  const calculateMetrics = () => {
    const total = holdings.reduce((sum, h) => sum + h.shares * h.pricePerShare, 0)
    const averagePrice = holdings.length > 0 ? total / holdings.length : 0

    return {
      totalValue: total,
      averagePrice,
      holdingCount: holdings.length,
      allocation: holdings.map((h) => ({
        ticker: h.ticker,
        percentage: ((h.shares * h.pricePerShare) / total) * 100,
        value: h.shares * h.pricePerShare,
      })),
    }
  }

  const metrics = calculateMetrics()
  const totalValue = metrics.totalValue

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Portfolio Manager</h2>
        <p className="text-sm text-gray-600 mt-1">Add and manage your investment holdings</p>
      </div>

      {/* Input Form */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-3">
          {/* Ticker Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ticker</label>
            <input
              type="text"
              placeholder="AAPL"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 text-sm ${
                errors.ticker ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
              }`}
            />
            {errors.ticker && <p className="text-xs text-red-600 mt-1">{errors.ticker}</p>}
          </div>

          {/* Shares Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Shares</label>
            <input
              type="number"
              placeholder="100"
              value={shares}
              onChange={(e) => setShares(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 text-sm ${
                errors.shares ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
              }`}
            />
            {errors.shares && <p className="text-xs text-red-600 mt-1">{errors.shares}</p>}
          </div>

          {/* Current Price Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Price</label>
            <input
              type="number"
              placeholder="150.25"
              value={pricePerShare}
              onChange={(e) => setPricePerShare(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 text-sm ${
                errors.price ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
              }`}
            />
            {errors.price && <p className="text-xs text-red-600 mt-1">{errors.price}</p>}
          </div>

          {/* Cost Basis Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cost Basis <span className="text-gray-500 text-xs">(optional)</span></label>
            <input
              type="number"
              placeholder="Leave empty = current price"
              value={costBasis}
              onChange={(e) => setCostBasis(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 text-sm ${
                errors.costBasis ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
              }`}
            />
            {errors.costBasis && <p className="text-xs text-red-600 mt-1">{errors.costBasis}</p>}
          </div>

          {/* Add Button */}
          <div className="flex items-end">
            <button
              onClick={handleAddHolding}
              className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add
            </button>
          </div>
        </div>

        {errors.total && (
          <p className="text-sm text-red-600 mb-3 p-2 bg-red-50 rounded">⚠️ {errors.total}</p>
        )}
      </div>

      {/* Holdings List */}
      {holdings.length > 0 ? (
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-xs text-gray-600 mb-1">Total Value</p>
              <p className="text-2xl font-bold text-blue-600">${totalValue.toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-xs text-gray-600 mb-1">Holdings</p>
              <p className="text-2xl font-bold text-green-600">{holdings.length}</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-xs text-gray-600 mb-1">Avg Price</p>
              <p className="text-2xl font-bold text-purple-600">${metrics.averagePrice.toFixed(2)}</p>
            </div>
          </div>

          {/* Holdings Table */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Ticker</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Shares</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Price/Share</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Value</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">%</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding) => {
                  const value = holding.shares * holding.pricePerShare
                  const percentage = totalValue > 0 ? ((value / totalValue) * 100).toFixed(1) : '0'
                  return (
                    <tr key={holding.id} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-semibold text-gray-900">{holding.ticker}</td>
                      <td className="px-4 py-3 text-right text-gray-700">{holding.shares.toLocaleString()}</td>
                      <td className="px-4 py-3 text-right text-gray-700">${holding.pricePerShare.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">
                        ${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                          {percentage}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => handleRemoveHolding(holding.id)}
                          className="text-red-600 hover:text-red-700 font-medium text-sm hover:bg-red-50 px-2 py-1 rounded transition-colors"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Allocation Breakdown */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Allocation Breakdown</h3>
            <div className="space-y-2">
              {metrics.allocation.map((alloc) => (
                <div key={alloc.ticker}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-medium text-sm text-gray-700">{alloc.ticker}</span>
                    <span className="text-sm text-gray-600">{alloc.percentage.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${alloc.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600">No holdings added yet. Add your first holding above!</p>
        </div>
      )}
    </div>
  )
}

export default PortfolioForm
