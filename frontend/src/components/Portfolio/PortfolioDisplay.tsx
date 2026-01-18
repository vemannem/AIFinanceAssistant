import { FC, useMemo } from 'react'
import { usePortfolioStore } from '../../store/portfolioStore'

interface AllocationData {
  name: string
  value: number
  percentage: string
}

/**
 * PortfolioDisplay Component
 * Shows portfolio metrics and allocation visualization
 * Uses SVG for chart rendering (no external chart library needed yet)
 */
export const PortfolioDisplay: FC = () => {
  const store = usePortfolioStore()
  const holdings = store.holdings || []

  // Calculate metrics
  const metrics = useMemo(() => {
    const totalValue = holdings.reduce((sum, h) => sum + (h.amount || 0), 0)
    const allocationData: AllocationData[] = holdings
      .map((h) => ({
        name: h.ticker,
        value: h.amount || 0,
        percentage: totalValue > 0 ? (((h.amount || 0) / totalValue) * 100).toFixed(1) : '0',
      }))
      .sort((a, b) => b.value - a.value)

    return {
      totalValue,
      holdingCount: holdings.length,
      largestPosition: allocationData[0],
      smallestPosition: allocationData[allocationData.length - 1],
      allocationData,
      diversificationScore: calculateDiversificationScore(allocationData),
    }
  }, [holdings])

  // Calculate diversification score (0-100)
  // Higher score = better diversification
  const calculateDiversificationScore = (data: AllocationData[]): number => {
    if (data.length === 0) return 0

    // Herfindahl index
    const herfindahl = data.reduce((sum, item) => {
      const pct = parseFloat(item.percentage) / 100
      return sum + pct * pct
    }, 0)

    // Convert to 0-100 scale (1 = perfect concentration, 0 = perfect diversity)
    const diversity = (1 - herfindahl) * 100
    return Math.min(100, diversity)
  }

  // Generate color for chart
  const getColor = (index: number): string => {
    const colors = [
      '#3b82f6', // blue
      '#10b981', // green
      '#f59e0b', // amber
      '#ef4444', // red
      '#8b5cf6', // purple
      '#06b6d4', // cyan
      '#ec4899', // pink
      '#6366f1', // indigo
    ]
    return colors[index % colors.length]
  }

  // Pie chart SVG
  const renderPieChart = () => {
    const data = metrics.allocationData
    const size = 200
    const radius = 80

    let currentAngle = -Math.PI / 2
    const paths: Array<{ path: string; color: string; label: string }> = []

    data.forEach((item, index) => {
      const slicePercent = parseFloat(item.percentage) / 100
      const sliceAngle = slicePercent * 2 * Math.PI

      const x1 = size / 2 + radius * Math.cos(currentAngle)
      const y1 = size / 2 + radius * Math.sin(currentAngle)

      const x2 = size / 2 + radius * Math.cos(currentAngle + sliceAngle)
      const y2 = size / 2 + radius * Math.sin(currentAngle + sliceAngle)

      const largeArc = sliceAngle > Math.PI ? 1 : 0

      const path = `M ${size / 2} ${size / 2} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`

      paths.push({
        path,
        color: getColor(index),
        label: item.name,
      })

      currentAngle += sliceAngle
    })

    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="mx-auto">
        {paths.map((p, i) => (
          <path key={i} d={p.path} fill={p.color} stroke="white" strokeWidth="2" />
        ))}
      </svg>
    )
  }

  if (holdings.length === 0) {
    return (
      <div className="text-center py-8 bg-gray-50 rounded-lg">
        <p className="text-gray-600">No holdings added yet. Add holdings using the form above!</p>
      </div>
    )
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Portfolio Analysis</h2>
        <p className="text-sm text-gray-600 mt-1">View your portfolio metrics and allocation</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <p className="text-xs text-gray-600 mb-1">Total Value</p>
          <p className="text-2xl font-bold text-blue-600">
            ${metrics.totalValue.toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </p>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <p className="text-xs text-gray-600 mb-1">Holdings</p>
          <p className="text-2xl font-bold text-green-600">{metrics.holdingCount}</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
          <p className="text-xs text-gray-600 mb-1">Diversification</p>
          <p className="text-2xl font-bold text-purple-600">{metrics.diversificationScore.toFixed(0)}/100</p>
        </div>

        <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-4">
          <p className="text-xs text-gray-600 mb-1">Largest Position</p>
          <p className="text-xl font-bold text-amber-600">
            {metrics.largestPosition?.name || 'N/A'} ({metrics.largestPosition?.percentage || '0'}%)
          </p>
        </div>
      </div>

      {/* Charts and Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pie Chart */}
        <div className="lg:col-span-1 bg-white border border-gray-200 rounded-lg p-6 flex flex-col items-center justify-center">
          <h3 className="font-semibold text-gray-900 mb-4">Allocation</h3>
          {renderPieChart()}
        </div>

        {/* Legend and Details */}
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Holdings Breakdown</h3>
          <div className="space-y-3">
            {metrics.allocationData.map((item, index) => (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getColor(index) }}
                  />
                  <span className="font-medium text-gray-900">{item.name}</span>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-600 min-w-24 text-right">
                    ${item.value.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                  </span>
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${item.percentage}%`,
                        backgroundColor: getColor(index),
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-700 min-w-12 text-right">{item.percentage}%</span>
                </div>
              </div>
            ))}
          </div>

          {/* Diversification Indicator */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Diversification Score</span>
              <span className="text-sm font-bold text-gray-900">{metrics.diversificationScore.toFixed(0)}/100</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="h-3 rounded-full transition-all"
                style={{
                  width: `${metrics.diversificationScore}%`,
                  backgroundColor:
                    metrics.diversificationScore >= 70
                      ? '#10b981'
                      : metrics.diversificationScore >= 40
                        ? '#f59e0b'
                        : '#ef4444',
                }}
              />
            </div>
            <p className="text-xs text-gray-600 mt-2">
              {metrics.diversificationScore >= 70
                ? '✅ Well diversified'
                : metrics.diversificationScore >= 40
                  ? '⚠️ Moderate diversification'
                  : '❌ High concentration risk'}
            </p>
          </div>
        </div>
      </div>

      {/* Risk Assessment */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Risk Assessment</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>✓ Total Portfolio Value: ${metrics.totalValue.toLocaleString('en-US', { maximumFractionDigits: 2 })}</li>
          <li>✓ Number of Holdings: {metrics.holdingCount}</li>
          <li>✓ Largest Concentration: {metrics.largestPosition?.percentage}% in {metrics.largestPosition?.name}</li>
          <li>
            ✓ Diversification Score: {metrics.diversificationScore >= 70 ? 'Good ✅' : metrics.diversificationScore >= 40 ? 'Fair ⚠️' : 'Poor ❌'}
          </li>
        </ul>
      </div>
    </div>
  )
}

export default PortfolioDisplay
