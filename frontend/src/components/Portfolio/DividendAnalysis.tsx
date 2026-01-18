import { FC, useMemo, useEffect, useState } from 'react'
import { usePortfolioStore } from '../../store/portfolioStore'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import axios from 'axios'

interface Holding {
  ticker: string
  shares: number
  pricePerShare: number
}

interface RealTimePrice {
  [ticker: string]: number
}

export const DividendAnalysis: FC = () => {
  const { holdings } = usePortfolioStore()
  const [realPrices, setRealPrices] = useState<RealTimePrice>({})
  const [dividendData, setDividendData] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(false)

  // Fetch real-time data (prices + dividends) from unified market API
  useEffect(() => {
    if (holdings.length === 0) return

    const fetchData = async () => {
      setLoading(true)
      try {
        const tickers = holdings.map(h => h.ticker)
        
        // Single API call gets both market prices AND dividend data
        const response = await axios.post('http://localhost:8000/api/market/quotes', {
          tickers
        })
        
        const prices: RealTimePrice = {}
        const dividends: Record<string, any> = {}
        
        Object.entries(response.data.quotes).forEach(([ticker, data]: [string, any]) => {
          prices[ticker] = data.price
          dividends[ticker] = {
            yield: data.dividend_yield,
            frequency: data.dividend_frequency,
            nextPayDate: data.next_dividend_date,
            annualDividend: data.annual_dividend_per_share,
          }
        })
        
        setRealPrices(prices)
        setDividendData(dividends)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [holdings])

  // Mock dividend data (fallback)
  const mockDividendData: Record<string, { yield: number; frequency: string; nextPayDate: string }> = {
    'AAPL': { yield: 0.5, frequency: 'Quarterly', nextPayDate: '2026-02-15' },
    'MSFT': { yield: 0.84, frequency: 'Quarterly', nextPayDate: '2026-02-20' },
    'JPM': { yield: 2.5, frequency: 'Quarterly', nextPayDate: '2026-01-20' },
    'JNJ': { yield: 2.8, frequency: 'Quarterly', nextPayDate: '2026-03-01' },
    'BND': { yield: 4.2, frequency: 'Monthly', nextPayDate: '2026-01-31' },
    'AGG': { yield: 3.8, frequency: 'Monthly', nextPayDate: '2026-01-31' },
    'PYPL': { yield: 0, frequency: 'None', nextPayDate: 'N/A' },
  }

  const dividendAnalysis = useMemo(() => {
    if (holdings.length === 0) return null

    // Use real-time prices if available
    const holdingsWithPrices = holdings.map(h => ({
      ...h,
      pricePerShare: realPrices[h.ticker] || h.pricePerShare,
    }))

    const holdingsWithDividends = holdingsWithPrices.map(h => {
      // Use real dividend data if available, otherwise use mock
      const divData = dividendData[h.ticker] || mockDividendData[h.ticker] || { yield: 0, frequency: 'None', nextPayDate: 'N/A', annualDividend: 0 }
      const annualDividendPerShare = divData.annualDividend || (h.pricePerShare * divData.yield) / 100
      const annualDividend = h.shares * annualDividendPerShare
      const quarterlyDividend = annualDividend / (divData.frequency === 'Quarterly' ? 4 : divData.frequency === 'Monthly' ? 12 : 1)

      return {
        ticker: h.ticker,
        shares: h.shares,
        price: h.pricePerShare,
        value: h.shares * h.pricePerShare,
        yield: divData.yield,
        frequency: divData.frequency,
        nextPayDate: divData.nextPayDate,
        annualDividend,
        monthlyDividend: annualDividend / 12,
        quarterlyDividend,
      }
    })

    const totalAnnualDividend = holdingsWithDividends.reduce((sum, h) => sum + h.annualDividend, 0)
    const totalMonthlyDividend = holdingsWithDividends.reduce((sum, h) => sum + h.monthlyDividend, 0)
    const portfolioValue = holdingsWithDividends.reduce((sum, h) => sum + h.value, 0)
    const weightedAvgYield = (totalAnnualDividend / portfolioValue) * 100

    // Generate 12-month projection
    const monthlyProjection = Array.from({ length: 12 }, (_, i) => {
      const month = new Date(2026, i)
      const monthName = month.toLocaleString('en-US', { month: 'short', year: '2-digit' })
      const dividendInMonth = holdingsWithDividends
        .filter(h => {
          if (h.frequency === 'Monthly') return h.monthlyDividend
          if (h.frequency === 'Quarterly') return [1, 4, 7, 10].includes(i + 1) ? h.quarterlyDividend : 0
          return 0
        })
        .reduce((sum, h) => {
          if (h.frequency === 'Monthly') return sum + h.monthlyDividend
          if (h.frequency === 'Quarterly' && [1, 4, 7, 10].includes(i + 1)) return sum + h.quarterlyDividend
          return sum
        }, 0)

      return {
        month: monthName,
        dividend: Math.round(dividendInMonth * 100) / 100,
      }
    })

    return {
      holdings: holdingsWithDividends.filter(h => h.annualDividend > 0),
      totalAnnualDividend,
      totalMonthlyDividend,
      portfolioValue,
      weightedAvgYield,
      monthlyProjection,
    }
  }, [holdings, realPrices, dividendData])

  if (!dividendAnalysis) {
    return <div className="text-center py-8 text-gray-500">No holdings to analyze</div>
  }

  return (
    <div className="space-y-6">
      {loading && <div className="text-sm text-blue-600 font-medium">📡 Updating market prices...</div>}
      {/* Dividend Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
          <p className="text-sm text-gray-600 mb-1">Annual Dividend Income</p>
          <p className="text-3xl font-bold text-green-600">${dividendAnalysis.totalAnnualDividend.toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
          <p className="text-xs text-gray-500 mt-2">Per year</p>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
          <p className="text-sm text-gray-600 mb-1">Monthly Dividend Income</p>
          <p className="text-3xl font-bold text-blue-600">${dividendAnalysis.totalMonthlyDividend.toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
          <p className="text-xs text-gray-500 mt-2">Average per month</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
          <p className="text-sm text-gray-600 mb-1">Weighted Avg Yield</p>
          <p className="text-3xl font-bold text-purple-600">{dividendAnalysis.weightedAvgYield.toFixed(2)}%</p>
          <p className="text-xs text-gray-500 mt-2">Portfolio dividend yield</p>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200">
          <p className="text-sm text-gray-600 mb-1">Dividend Stocks</p>
          <p className="text-3xl font-bold text-orange-600">{dividendAnalysis.holdings.length}</p>
          <p className="text-xs text-gray-500 mt-2">Paying dividends</p>
        </div>
      </div>

      {/* 12-Month Projection Chart */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">12-Month Dividend Projection</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dividendAnalysis.monthlyProjection}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip formatter={(value) => `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`} />
            <Legend />
            <Line
              type="monotone"
              dataKey="dividend"
              stroke="#10B981"
              dot={{ fill: '#10B981', r: 4 }}
              activeDot={{ r: 6 }}
              name="Projected Dividend"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Holdings Dividend Details */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Dividend-Paying Holdings</h3>
        {dividendAnalysis.holdings.length === 0 ? (
          <p className="text-gray-500 text-center py-8">None of your current holdings pay dividends</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Ticker</th>
                  <th className="px-4 py-3 text-right font-semibold">Shares</th>
                  <th className="px-4 py-3 text-right font-semibold">Price</th>
                  <th className="px-4 py-3 text-right font-semibold">Yield</th>
                  <th className="px-4 py-3 text-right font-semibold">Frequency</th>
                  <th className="px-4 py-3 text-right font-semibold">Annual Dividend</th>
                  <th className="px-4 py-3 text-right font-semibold">Monthly Income</th>
                  <th className="px-4 py-3 text-right font-semibold">Next Pay Date</th>
                </tr>
              </thead>
              <tbody>
                {dividendAnalysis.holdings.map((holding, idx) => (
                  <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 font-semibold">{holding.ticker}</td>
                    <td className="px-4 py-3 text-right">{holding.shares.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">${holding.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right text-green-600 font-semibold">{holding.yield.toFixed(2)}%</td>
                    <td className="px-4 py-3 text-right">{holding.frequency}</td>
                    <td className="px-4 py-3 text-right font-semibold">${holding.annualDividend.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right">${holding.monthlyDividend.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right text-sm">{holding.nextPayDate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Dividend Strategy Tips */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-emerald-900 mb-3">📊 Dividend Growth Strategy</h3>
        <ul className="space-y-2 text-sm text-emerald-800">
          <li>
            <strong>Current Income:</strong> Your portfolio generates ~${dividendAnalysis.totalMonthlyDividend.toLocaleString('en-US', { maximumFractionDigits: 2 })}/month in dividend income
          </li>
          <li>
            <strong>Dividend Reinvestment:</strong> Enable DRIP to compound growth (additional {(dividendAnalysis.weightedAvgYield * 0.5).toFixed(1)}% annual returns if reinvested)
          </li>
          <li>
            <strong>Dividend Growth Stocks:</strong> Add stocks with 5-10 year dividend growth history (e.g., JNJ, PG, KO)
          </li>
          <li>
            <strong>Tax Efficiency:</strong> Qualified dividends taxed at 15% (vs. regular income). Hold longer than 60 days around ex-date.
          </li>
          <li>
            <strong>Target Yield:</strong> For income, aim for 2-4% weighted yield (current: {dividendAnalysis.weightedAvgYield.toFixed(2)}%)
          </li>
        </ul>
      </div>
    </div>
  )
}

export default DividendAnalysis
