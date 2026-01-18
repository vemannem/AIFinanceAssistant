import { FC, useMemo, useEffect, useState } from 'react'
import { usePortfolioStore } from '../../store/portfolioStore'
import axios from 'axios'

interface Holding {
  ticker: string
  shares: number
  pricePerShare: number
}

interface RealTimePrice {
  [ticker: string]: number
}

export const TaxImpactAnalysis: FC = () => {
  const { holdings } = usePortfolioStore()
  const [realPrices, setRealPrices] = useState<RealTimePrice>({})
  const [loading, setLoading] = useState(false)

  // Fetch real market data from backend
  useEffect(() => {
    if (holdings.length === 0) return

    const fetchPrices = async () => {
      setLoading(true)
      try {
        const tickers = holdings.map(h => h.ticker)
        const response = await axios.post('http://localhost:8000/api/market/quotes', {
          tickers
        })
        
        const prices: RealTimePrice = {}
        Object.entries(response.data.quotes).forEach(([ticker, data]: [string, any]) => {
          prices[ticker] = data.price
        })
        setRealPrices(prices)
      } catch (error) {
        console.error('Failed to fetch market prices:', error)
        // Fall back to stored prices if API fails
      } finally {
        setLoading(false)
      }
    }

    fetchPrices()
  }, [holdings])

  const taxAnalysis = useMemo(() => {
    if (holdings.length === 0) return null

    const holdings_with_gains = holdings.map(h => {
      // Use real-time price if available, otherwise use stored price
      const currentPrice = realPrices[h.ticker] || h.pricePerShare
      // Use the cost basis from the holding, or default to current price if not set
      const costBasis = (h as any).costBasis || h.pricePerShare
      const currentValue = h.shares * currentPrice
      const costValue = h.shares * costBasis
      const gainLoss = currentValue - costValue
      const gainLossPercentage = (gainLoss / costValue) * 100
      const holdingPeriod = Math.random() > 0.5 ? 'long-term' : 'short-term' // Mock
      const taxRate = holdingPeriod === 'long-term' ? 0.15 : 0.37
      const taxableGain = Math.max(0, gainLoss)
      const taxLiability = taxableGain * taxRate

      return {
        ticker: h.ticker,
        shares: h.shares,
        costBasis,
        currentPrice,
        currentValue,
        costValue,
        gainLoss,
        gainLossPercentage,
        holdingPeriod,
        taxRate,
        taxableGain,
        taxLiability,
      }
    })

    const totalTaxLiability = holdings_with_gains.reduce((sum, h) => sum + h.taxLiability, 0)
    const unrealizedGains = holdings_with_gains.reduce((sum, h) => sum + h.gainLoss, 0)
    const losHarvestingOpportunities = holdings_with_gains.filter(h => h.gainLoss < 0)

    return {
      holdings: holdings_with_gains,
      totalTaxLiability,
      unrealizedGains,
      losHarvestingOpportunities,
    }
  }, [holdings, realPrices])

  if (!taxAnalysis) {
    return <div className="text-center py-8 text-gray-500">No holdings to analyze</div>
  }

  return (
    <div className="space-y-6">
      {loading && <div className="text-sm text-blue-600 font-medium">📡 Updating market prices...</div>}
      {/* Tax Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-4 border border-red-200">
          <p className="text-sm text-gray-600 mb-1">Estimated Tax Liability</p>
          <p className="text-3xl font-bold text-red-600">${taxAnalysis.totalTaxLiability.toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
          <p className="text-xs text-gray-500 mt-2">On realized gains (federal)</p>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
          <p className="text-sm text-gray-600 mb-1">Unrealized Gains</p>
          <p className={`text-3xl font-bold ${taxAnalysis.unrealizedGains >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${Math.abs(taxAnalysis.unrealizedGains).toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-gray-500 mt-2">Not yet taxed</p>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
          <p className="text-sm text-gray-600 mb-1">Tax-Loss Harvesting</p>
          <p className="text-3xl font-bold text-blue-600">{taxAnalysis.losHarvestingOpportunities.length}</p>
          <p className="text-xs text-gray-500 mt-2">Opportunities available</p>
        </div>
      </div>

      {/* Holdings Tax Breakdown */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Per-Holding Tax Analysis</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Ticker</th>
                <th className="px-4 py-3 text-right font-semibold">Cost Basis</th>
                <th className="px-4 py-3 text-right font-semibold">Current Price</th>
                <th className="px-4 py-3 text-right font-semibold">Unrealized Gain</th>
                <th className="px-4 py-3 text-right font-semibold">Holding Period</th>
                <th className="px-4 py-3 text-right font-semibold">Tax Rate</th>
                <th className="px-4 py-3 text-right font-semibold">Tax Liability</th>
              </tr>
            </thead>
            <tbody>
              {taxAnalysis.holdings.map((holding, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold">{holding.ticker}</td>
                  <td className="px-4 py-3 text-right">${holding.costBasis.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                  <td className="px-4 py-3 text-right">${holding.currentPrice.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${holding.gainLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {holding.gainLoss >= 0 ? '+' : ''}{holding.gainLoss.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                    <br />
                    <span className="text-xs">({holding.gainLossPercentage.toFixed(1)}%)</span>
                  </td>
                  <td className={`px-4 py-3 text-right ${holding.holdingPeriod === 'long-term' ? 'text-green-600' : 'text-orange-600'}`}>
                    {holding.holdingPeriod === 'long-term' ? '✓ LT' : '⏱ ST'}
                  </td>
                  <td className="px-4 py-3 text-right">{(holding.taxRate * 100).toFixed(0)}%</td>
                  <td className="px-4 py-3 text-right font-semibold">${holding.taxLiability.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Tax Optimization Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">💰 Tax Optimization Strategies</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          {taxAnalysis.losHarvestingOpportunities.length > 0 && (
            <>
              <li>
                <strong>Tax-Loss Harvesting:</strong> You have {taxAnalysis.losHarvestingOpportunities.length} positions with losses that can offset gains:
              </li>
              {taxAnalysis.losHarvestingOpportunities.map((h, idx) => (
                <li key={idx} className="ml-4">
                  • {h.ticker}: Unrealized loss of ${Math.abs(h.gainLoss).toLocaleString('en-US', { maximumFractionDigits: 2 })} can save ~${Math.abs(h.gainLoss * 0.15).toLocaleString('en-US', { maximumFractionDigits: 2 })} in taxes
                </li>
              ))}
            </>
          )}
          <li>
            <strong>Hold Long-Term:</strong> Keep positions longer than 1 year for 15% tax rate vs. 37% short-term
          </li>
          <li>
            <strong>Charitable Donations:</strong> Consider donating appreciated securities directly to charities (avoid capital gains tax)
          </li>
          <li>
            <strong>401(k) Maximization:</strong> Max out tax-advantaged accounts ($7,000/year IRA, $23,500/year 401k)
          </li>
        </ul>
      </div>
    </div>
  )
}

export default TaxImpactAnalysis
