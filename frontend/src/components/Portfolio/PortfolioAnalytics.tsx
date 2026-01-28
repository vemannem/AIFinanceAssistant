import { FC, useMemo, useEffect, useState } from 'react'
import { usePortfolioStore } from '../../store/portfolioStore'
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { orchestrationService } from '../../services/orchestrationService'

interface Holding {
  ticker: string
  shares: number
  pricePerShare: number
}

interface RealTimePrice {
  [ticker: string]: number
}

const COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#06B6D4', '#6366F1', '#14B8A6']

export const PortfolioAnalytics: FC = () => {
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
      } finally {
        setLoading(false)
      }
    }

    fetchPrices()
  }, [holdings])

  const analytics = useMemo(() => {
    if (holdings.length === 0) return null

    // Use real-time prices if available, otherwise use stored prices
    const holdingsWithPrices = holdings.map(h => ({
      ...h,
      pricePerShare: realPrices[h.ticker] || h.pricePerShare,
    }))

    const totalValue = holdingsWithPrices.reduce((sum, h) => sum + h.shares * h.pricePerShare, 0)
    const allocation = holdingsWithPrices.map((h, idx) => ({
      ticker: h.ticker,
      value: h.shares * h.pricePerShare,
      percentage: ((h.shares * h.pricePerShare) / totalValue) * 100,
      shares: h.shares,
      price: h.pricePerShare,
      color: COLORS[idx % COLORS.length],
    }))

    // Calculate Herfindahl index for diversification
    const diversificationScore = 100 - Math.min(
      100,
      allocation.reduce((sum, a) => sum + Math.pow(a.percentage, 2), 0) / 100
    )

    // Identify largest position
    const largestPosition = allocation[0]

    // Calculate asset class distribution (mock)
    const assetDistribution = {
      'Tech': allocation.filter(a => ['AAPL', 'MSFT', 'GOOGL', 'NVDA'].includes(a.ticker)).reduce((s, a) => s + a.percentage, 0),
      'Finance': allocation.filter(a => ['JPM', 'BAC', 'GS', 'PYPL'].includes(a.ticker)).reduce((s, a) => s + a.percentage, 0),
      'Healthcare': allocation.filter(a => ['JNJ', 'PFE', 'UNH'].includes(a.ticker)).reduce((s, a) => s + a.percentage, 0),
      'Bonds': allocation.filter(a => ['BND', 'AGG', 'TLT'].includes(a.ticker)).reduce((s, a) => s + a.percentage, 0),
      'Other': 100 - (allocation.filter(a => ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'JPM', 'BAC', 'GS', 'JNJ', 'PFE', 'UNH', 'BND', 'AGG', 'TLT', 'PYPL'].includes(a.ticker)).reduce((s, a) => s + a.percentage, 0)),
    }

    // Risk assessment
    const riskLevel = diversificationScore > 70 ? 'Low' : diversificationScore > 40 ? 'Moderate' : 'High'
    const stockPercentage = allocation.filter(a => !['BND', 'AGG', 'TLT'].includes(a.ticker)).reduce((s, a) => s + a.percentage, 0)
    const concentrationRisk = largestPosition.percentage > 30 ? 'High' : largestPosition.percentage > 20 ? 'Medium' : 'Low'

    return {
      totalValue,
      allocation: allocation.sort((a, b) => b.percentage - a.percentage),
      diversificationScore,
      largestPosition,
      assetDistribution,
      riskLevel,
      stockPercentage,
      concentrationRisk,
    }
  }, [holdings, realPrices])

  if (!analytics) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <p className="text-gray-600">No portfolio data. Add holdings to see analysis.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {loading && <div className="text-sm text-blue-600 font-medium">📡 Updating market prices...</div>}
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
          <p className="text-sm text-gray-600 mb-1">Total Portfolio Value</p>
          <p className="text-3xl font-bold text-blue-600">${analytics.totalValue.toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
          <p className="text-xs text-gray-500 mt-2">{holdings.length} holdings</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
          <p className="text-sm text-gray-600 mb-1">Diversification Score</p>
          <p className="text-3xl font-bold text-purple-600">{analytics.diversificationScore.toFixed(0)}/100</p>
          <p className="text-xs text-gray-500 mt-2">Risk: {analytics.riskLevel}</p>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
          <p className="text-sm text-gray-600 mb-1">Largest Position</p>
          <p className="text-3xl font-bold text-green-600">{analytics.largestPosition.percentage.toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-2">{analytics.largestPosition.ticker}</p>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200">
          <p className="text-sm text-gray-600 mb-1">Concentration Risk</p>
          <p className={`text-3xl font-bold ${analytics.concentrationRisk === 'High' ? 'text-orange-600' : 'text-orange-500'}`}>
            {analytics.concentrationRisk}
          </p>
          <p className="text-xs text-gray-500 mt-2">Top holding impact</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Allocation Pie Chart */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Allocation</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analytics.allocation}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ ticker, percentage }) => `${ticker} ${percentage.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {analytics.allocation.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Asset Class Distribution */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Class Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(analytics.assetDistribution).map(([name, value]) => ({ name, value }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
              <Bar dataKey="value" fill="#8B5CF6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Holdings Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Ticker</th>
                <th className="px-4 py-3 text-right font-semibold">Shares</th>
                <th className="px-4 py-3 text-right font-semibold">Price</th>
                <th className="px-4 py-3 text-right font-semibold">Value</th>
                <th className="px-4 py-3 text-right font-semibold">Allocation</th>
              </tr>
            </thead>
            <tbody>
              {analytics.allocation.map((holding, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold">{holding.ticker}</td>
                  <td className="px-4 py-3 text-right">{holding.shares.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right">${holding.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                  <td className="px-4 py-3 text-right font-semibold">${holding.value.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <span className="font-semibold">{holding.percentage.toFixed(1)}%</span>
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${holding.percentage}%` }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Risk Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-yellow-900 mb-3">⚠️ Risk Warnings</h3>
          <ul className="space-y-2 text-sm text-yellow-800">
            {analytics.concentrationRisk === 'High' && (
              <li>• High concentration risk: {analytics.largestPosition.ticker} represents {analytics.largestPosition.percentage.toFixed(1)}% of portfolio</li>
            )}
            {analytics.diversificationScore < 40 && (
              <li>• Low diversification: Consider adding more holdings to spread risk</li>
            )}
            {analytics.stockPercentage > 90 && (
              <li>• High equity exposure: Consider adding bonds for stability</li>
            )}
            {analytics.allocation.length < 3 && (
              <li>• Consider adding 2-3 more holdings for better diversification</li>
            )}
            {analytics.concentrationRisk !== 'High' && analytics.diversificationScore >= 40 && analytics.stockPercentage <= 90 && analytics.allocation.length >= 3 && (
              <li>✓ Portfolio structure looks well-balanced</li>
            )}
          </ul>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-3">💡 Recommendations</h3>
          <ul className="space-y-2 text-sm text-green-800">
            {analytics.largestPosition.percentage > 30 && (
              <li>• Consider rebalancing {analytics.largestPosition.ticker} to reduce concentration</li>
            )}
            {analytics.diversificationScore < 50 && (
              <li>• Add sector diversification with ETFs (SPY, QQQ, BND)</li>
            )}
            {analytics.stockPercentage > 80 && (
              <li>• Target 70/30 stock/bond allocation for stability</li>
            )}
            {analytics.allocation.length >= 3 && analytics.diversificationScore >= 60 && (
              <li>✓ Good portfolio structure - maintain and rebalance annually</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  )
}

export default PortfolioAnalytics
