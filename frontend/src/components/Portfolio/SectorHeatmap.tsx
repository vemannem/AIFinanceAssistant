import { FC, useMemo, useEffect, useState } from 'react'
import { usePortfolioStore } from '../../store/portfolioStore'
import { orchestrationService } from '../../services/orchestrationService'

interface Holding {
  ticker: string
  shares: number
  pricePerShare: number
}

interface RealTimePrice {
  [ticker: string]: number
}

// Mock sector and industry data
const TICKER_SECTOR_MAP: Record<string, { sector: string; industry: string; performance1Y: number }> = {
  'AAPL': { sector: 'Technology', industry: 'Consumer Electronics', performance1Y: 28.5 },
  'MSFT': { sector: 'Technology', industry: 'Software', performance1Y: 26.3 },
  'GOOGL': { sector: 'Technology', industry: 'Internet Services', performance1Y: 42.1 },
  'NVDA': { sector: 'Technology', industry: 'Semiconductors', performance1Y: 189.5 },
  'TSLA': { sector: 'Consumer Cyclical', industry: 'Automotive', performance1Y: -12.3 },
  'JPM': { sector: 'Financials', industry: 'Banking', performance1Y: 18.7 },
  'BAC': { sector: 'Financials', industry: 'Banking', performance1Y: 22.1 },
  'JNJ': { sector: 'Healthcare', industry: 'Pharmaceuticals', performance1Y: 2.1 },
  'PFE': { sector: 'Healthcare', industry: 'Pharmaceuticals', performance1Y: -23.5 },
  'UNH': { sector: 'Healthcare', industry: 'Healthcare Services', performance1Y: 18.9 },
  'BND': { sector: 'Fixed Income', industry: 'Bonds', performance1Y: 2.3 },
  'AGG': { sector: 'Fixed Income', industry: 'Bonds', performance1Y: 3.1 },
  'TLT': { sector: 'Fixed Income', industry: 'Treasury Bonds', performance1Y: 4.5 },
  'XOM': { sector: 'Energy', industry: 'Oil & Gas', performance1Y: 45.2 },
  'CVX': { sector: 'Energy', industry: 'Oil & Gas', performance1Y: 42.8 },
  'PYPL': { sector: 'Financials', industry: 'Fintech', performance1Y: -15.3 },
}

const SECTOR_COLORS: Record<string, string> = {
  'Technology': '#3B82F6',
  'Financials': '#8B5CF6',
  'Healthcare': '#10B981',
  'Consumer Cyclical': '#F59E0B',
  'Energy': '#EF4444',
  'Fixed Income': '#06B6D4',
  'Industrials': '#6366F1',
  'Consumer Staples': '#EC4899',
  'Real Estate': '#14B8A6',
  'Utilities': '#84CC16',
  'Materials': '#F97316',
  'Communications': '#06B6D4',
}

export const SectorHeatmap: FC = () => {
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

  const sectorAnalysis = useMemo(() => {
    if (holdings.length === 0) return null

    // Use real-time prices if available
    const holdingsWithPrices = holdings.map(h => ({
      ...h,
      pricePerShare: realPrices[h.ticker] || h.pricePerShare,
    }))

    const totalPortfolioValue = holdings.reduce((sum, h) => sum + h.shares * h.pricePerShare, 0)

    const sectorBreakdown: Record<string, { value: number; percentage: number; holdings: any[]; avgPerformance: number }> = {}
    const industryBreakdown: Record<string, { value: number; percentage: number; holdings: any[]; sector: string; avgPerformance: number }> = {}

    holdings.forEach(h => {
      const positionValue = h.shares * h.pricePerShare
      const sectorData = TICKER_SECTOR_MAP[h.ticker] || { sector: 'Other', industry: 'Unknown', performance1Y: 0 }

      if (!sectorBreakdown[sectorData.sector]) {
        sectorBreakdown[sectorData.sector] = { value: 0, percentage: 0, holdings: [], avgPerformance: 0 }
      }

      sectorBreakdown[sectorData.sector].value += positionValue
      sectorBreakdown[sectorData.sector].holdings.push({ ticker: h.ticker, value: positionValue, ...sectorData })

      if (!industryBreakdown[sectorData.industry]) {
        industryBreakdown[sectorData.industry] = { value: 0, percentage: 0, holdings: [], sector: sectorData.sector, avgPerformance: 0 }
      }
      industryBreakdown[sectorData.industry].value += positionValue
      industryBreakdown[sectorData.industry].holdings.push({ ticker: h.ticker, value: positionValue, ...sectorData })
    })

    // Calculate percentages and average performance
    Object.keys(sectorBreakdown).forEach(sector => {
      sectorBreakdown[sector].percentage = (sectorBreakdown[sector].value / totalPortfolioValue) * 100
      sectorBreakdown[sector].avgPerformance =
        sectorBreakdown[sector].holdings.reduce((sum, h) => sum + h.performance1Y, 0) / sectorBreakdown[sector].holdings.length
    })

    Object.keys(industryBreakdown).forEach(industry => {
      industryBreakdown[industry].percentage = (industryBreakdown[industry].value / totalPortfolioValue) * 100
      industryBreakdown[industry].avgPerformance =
        industryBreakdown[industry].holdings.reduce((sum, h) => sum + h.performance1Y, 0) / industryBreakdown[industry].holdings.length
    })

    return {
      sectors: Object.entries(sectorBreakdown)
        .map(([name, data]) => ({ name, ...data }))
        .sort((a, b) => b.percentage - a.percentage),
      industries: Object.entries(industryBreakdown)
        .map(([name, data]) => ({ name, ...data }))
        .sort((a, b) => b.percentage - a.percentage),
      totalValue: totalPortfolioValue,
    }
  }, [holdings, realPrices])

  if (!sectorAnalysis) {
    return <div className="text-center py-8 text-gray-500">No holdings to analyze</div>
  }

  const getPerformanceColor = (performance: number) => {
    if (performance > 20) return 'bg-green-100 border-green-300'
    if (performance > 0) return 'bg-emerald-50 border-emerald-200'
    if (performance > -10) return 'bg-orange-50 border-orange-200'
    return 'bg-red-100 border-red-300'
  }

  const getPerformanceTextColor = (performance: number) => {
    if (performance > 20) return 'text-green-700'
    if (performance > 0) return 'text-emerald-700'
    if (performance > -10) return 'text-orange-700'
    return 'text-red-700'
  }

  return (
    <div className="space-y-6">
      {loading && <div className="text-sm text-blue-600 font-medium">📡 Updating market prices...</div>}
      {/* Sector Heatmap Visualization */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">📊 Sector Heatmap</h3>

        {/* Sector Grid */}
        <div className="mb-8">
          <h4 className="text-md font-semibold text-gray-700 mb-4">By Sector</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sectorAnalysis.sectors.map((sector, idx) => (
              <div
                key={idx}
                className={`rounded-lg p-4 border-2 ${getPerformanceColor(sector.avgPerformance)}`}
                style={{
                  background: `linear-gradient(135deg, ${SECTOR_COLORS[sector.name]}20 0%, ${SECTOR_COLORS[sector.name]}05 100%)`,
                  borderColor: SECTOR_COLORS[sector.name],
                }}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <p className="font-semibold text-gray-900">{sector.name}</p>
                    <p className="text-sm text-gray-600">{sector.holdings.length} holdings</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold" style={{ color: SECTOR_COLORS[sector.name] }}>
                      {sector.percentage.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500">${sector.value.toLocaleString('en-US', { maximumFractionDigits: 0 })}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-gray-300">
                  <span className="text-xs font-semibold text-gray-600">1Y Performance</span>
                  <span className={`text-sm font-bold ${getPerformanceTextColor(sector.avgPerformance)}`}>
                    {sector.avgPerformance >= 0 ? '+' : ''}{sector.avgPerformance.toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Industry Breakdown */}
        <div>
          <h4 className="text-md font-semibold text-gray-700 mb-4">By Industry</h4>
          <div className="space-y-3">
            {sectorAnalysis.industries.map((industry, idx) => (
              <div key={idx} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ background: SECTOR_COLORS[industry.sector] }}
                />
                <div className="flex-grow">
                  <p className="font-semibold text-gray-900">{industry.name}</p>
                  <p className="text-xs text-gray-500">{industry.sector}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="font-semibold text-gray-900">{industry.percentage.toFixed(1)}%</p>
                  <p className={`text-sm font-semibold ${getPerformanceTextColor(industry.avgPerformance)}`}>
                    {industry.avgPerformance >= 0 ? '+' : ''}{industry.avgPerformance.toFixed(1)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sector Concentration Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">⚠️ Concentration Risks</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            {sectorAnalysis.sectors.map((sector, idx) => {
              if (sector.percentage > 30) {
                return (
                  <li key={idx}>
                    • <strong>{sector.name}</strong> is {sector.percentage.toFixed(1)}% of portfolio - consider rebalancing
                  </li>
                )
              }
              return null
            })}
            {sectorAnalysis.sectors.filter(s => s.percentage > 30).length === 0 && (
              <li>✓ Sector diversification looks good - no major concentration</li>
            )}
          </ul>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-3">💡 Sector Opportunities</h3>
          <ul className="space-y-2 text-sm text-green-800">
            {sectorAnalysis.sectors
              .filter(s => s.percentage < 10)
              .map((sector, idx) => (
                <li key={idx}>
                  • <strong>{sector.name}</strong>: Underweight ({sector.percentage.toFixed(1)}%) - consider adding for diversification
                </li>
              ))}
            {sectorAnalysis.sectors.filter(s => s.percentage < 10).length === 0 && (
              <li>✓ All major sectors represented in portfolio</li>
            )}
          </ul>
        </div>
      </div>

      {/* Sector Performance Comparison */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Sector Performance (1Y)</h3>
        <div className="space-y-3">
          {sectorAnalysis.sectors.map((sector, idx) => (
            <div key={idx} className="flex items-center gap-4">
              <div className="w-32">
                <p className="font-semibold text-gray-900">{sector.name}</p>
              </div>
              <div className="flex-grow bg-gray-200 rounded-full h-8 flex items-center overflow-hidden">
                <div
                  className="h-full flex items-center justify-center text-white text-xs font-bold"
                  style={{
                    width: `${Math.min(100, Math.max(5, 50 + sector.avgPerformance))}%`,
                    background: sector.avgPerformance >= 0 ? '#10B981' : '#EF4444',
                  }}
                >
                  {Math.abs(sector.avgPerformance).toFixed(0)}%
                </div>
              </div>
              <div className="w-16 text-right">
                <p className={`font-bold ${getPerformanceTextColor(sector.avgPerformance)}`}>
                  {sector.avgPerformance >= 0 ? '+' : ''}{sector.avgPerformance.toFixed(1)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sector Strategy Tips */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-indigo-900 mb-3">🎯 Sector Strategy Tips</h3>
        <ul className="space-y-2 text-sm text-indigo-800">
          <li>
            <strong>Diversification Target:</strong> Aim for 10-15% per sector (current largest: {sectorAnalysis.sectors[0].percentage.toFixed(1)}%)
          </li>
          <li>
            <strong>Cyclical vs. Defensive:</strong> Mix growth sectors (Tech) with defensive sectors (Healthcare, Utilities, Consumer Staples)
          </li>
          <li>
            <strong>Economic Cycle:</strong> During expansion: increase tech/cyclical. During contraction: increase bonds/utilities
          </li>
          <li>
            <strong>Rebalancing:</strong> Review quarterly and rebalance when any sector drifts more than 5% from target allocation
          </li>
          <li>
            <strong>Market Rotation:</strong> Top performers today may underperform tomorrow - maintain discipline in diversification
          </li>
        </ul>
      </div>
    </div>
  )
}

export default SectorHeatmap
