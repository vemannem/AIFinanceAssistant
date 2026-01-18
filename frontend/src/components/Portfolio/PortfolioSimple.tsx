import { FC, useState, useRef } from 'react'
import { usePortfolioStore } from '../../store/portfolioStore'

interface Holding {
  ticker: string
  shares: number
  price: number
}

export const PortfolioSimple: FC = () => {
  const { holdings, addHolding, removeHolding } = usePortfolioStore()
  const [ticker, setTicker] = useState('')
  const [shares, setShares] = useState('')
  const [price, setPrice] = useState('')
  const [csvError, setCsvError] = useState('')
  const [csvSuccess, setCsvSuccess] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleAdd = () => {
    if (!ticker || !shares || !price) {
      alert('Please fill in all fields')
      return
    }

    addHolding({
      ticker: ticker.toUpperCase(),
      shares: parseFloat(shares),
      pricePerShare: parseFloat(price),
    })

    setTicker('')
    setShares('')
    setPrice('')
  }

  const handleCSVUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        setCsvError('')
        setCsvSuccess('')
        const csv = e.target?.result as string
        
        // Handle both \r\n and \n line endings
        const lines = csv.split(/\r?\n/).map(line => line.trim()).filter(line => line.length > 0)
        
        if (lines.length < 2) {
          setCsvError('CSV must have header and at least one data row')
          return
        }

        // Parse header - more robust parsing
        const headerLine = lines[0]
        const header = headerLine.split(',').map(h => h.trim().toLowerCase())
        
        // Find column indices with more flexible matching
        const tickerIdx = header.findIndex(h => h === 'ticker' || h === 'symbol' || h === 'tick')
        const shareIdx = header.findIndex(h => h === 'shares' || h === 'quantity' || h === 'qty' || h === 'share')
        const priceIdx = header.findIndex(h => h === 'price' || h === 'current_price' || h === 'current price')

        // Debug: log what we found
        console.log('Header:', header)
        console.log('Indices - ticker:', tickerIdx, 'shares:', shareIdx, 'price:', priceIdx)

        if (tickerIdx === -1 || shareIdx === -1 || priceIdx === -1) {
          setCsvError(`❌ Column not found. Found: ${header.join(', ')}. Need: ticker, shares, price`)
          return
        }

        // Parse data rows
        let addedCount = 0
        const errors = []
        
        for (let i = 1; i < lines.length; i++) {
          const line = lines[i].trim()
          if (!line) continue

          const cols = line.split(',').map(c => c.trim())
          
          if (cols.length < Math.max(tickerIdx, shareIdx, priceIdx) + 1) {
            errors.push(`Row ${i + 1}: not enough columns`)
            continue
          }
          
          const tickerVal = cols[tickerIdx]?.toUpperCase()
          const shareVal = parseFloat(cols[shareIdx])
          const priceVal = parseFloat(cols[priceIdx])

          if (tickerVal && !isNaN(shareVal) && !isNaN(priceVal)) {
            addHolding({
              ticker: tickerVal,
              shares: shareVal,
              pricePerShare: priceVal,
            })
            addedCount++
          } else {
            errors.push(`Row ${i + 1}: invalid data (${tickerVal}, ${cols[shareIdx]}, ${cols[priceIdx]})`)
          }
        }

        if (addedCount > 0) {
          setCsvSuccess(`✓ Successfully added ${addedCount} holding${addedCount !== 1 ? 's' : ''}`)
        } else {
          setCsvError('No valid rows found in CSV')
        }
        
        if (errors.length > 0 && errors.length <= 3) {
          console.warn('CSV parsing warnings:', errors)
        }
        
        if (fileInputRef.current) fileInputRef.current.value = ''
      } catch (err) {
        setCsvError(`❌ Error parsing CSV: ${err instanceof Error ? err.message : 'Unknown error'}`)
      }
    }
    reader.readAsText(file)
  }

  const totalValue = holdings.reduce((sum, h) => sum + h.shares * h.pricePerShare, 0)

  return (
    <div className="w-full">
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">📊 Portfolio</h2>

        {/* Input Form */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-6 p-4 bg-blue-50 rounded-lg">
          <div>
            <label className="text-sm font-medium block mb-1">Ticker</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
              className="w-full px-3 py-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <label className="text-sm font-medium block mb-1">Shares</label>
            <input
              type="number"
              value={shares}
              onChange={(e) => setShares(e.target.value)}
              placeholder="100"
              className="w-full px-3 py-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <label className="text-sm font-medium block mb-1">Price</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="150.50"
              className="w-full px-3 py-2 border border-gray-300 rounded"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleAdd}
              className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded hover:bg-blue-700"
            >
              Add
            </button>
          </div>
        </div>

        {/* CSV Upload Section */}
        <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border-2 border-dashed border-purple-300">
          <div className="flex flex-col gap-3">
            <div>
              <label className="text-sm font-semibold text-gray-900 block mb-2">📥 Or upload CSV file:</label>
              <p className="text-xs text-gray-600 mb-3">CSV columns: ticker, shares (or quantity), price</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleCSVUpload}
                className="w-full px-3 py-2 border border-purple-300 rounded bg-white cursor-pointer hover:bg-purple-50"
              />
            </div>
            {csvError && (
              <div className="p-3 bg-red-100 border border-red-400 text-red-800 rounded text-sm">
                ❌ {csvError}
              </div>
            )}
            {csvSuccess && (
              <div className="p-3 bg-green-100 border border-green-400 text-green-800 rounded text-sm">
                {csvSuccess}
              </div>
            )}
          </div>
        </div>

        {/* Holdings Table */}
        {holdings.length > 0 ? (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                <p className="text-xs text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-blue-600">${totalValue.toFixed(2)}</p>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                <p className="text-xs text-gray-600">Holdings</p>
                <p className="text-2xl font-bold text-green-600">{holdings.length}</p>
              </div>
            </div>

            <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left">Ticker</th>
                  <th className="px-4 py-2 text-right">Shares</th>
                  <th className="px-4 py-2 text-right">Price</th>
                  <th className="px-4 py-2 text-right">Value</th>
                  <th className="px-4 py-2 text-right">%</th>
                  <th className="px-4 py-2 text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((h, idx) => (
                  <tr key={idx} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 font-semibold">{h.ticker}</td>
                    <td className="px-4 py-2 text-right">{h.shares.toLocaleString()}</td>
                    <td className="px-4 py-2 text-right">${h.pricePerShare.toFixed(2)}</td>
                    <td className="px-4 py-2 text-right font-semibold">${(h.shares * h.pricePerShare).toFixed(2)}</td>
                    <td className="px-4 py-2 text-right">{((h.shares * h.pricePerShare / totalValue) * 100).toFixed(1)}%</td>
                    <td className="px-4 py-2 text-center">
                      <button
                        onClick={() => removeHolding(idx)}
                        className="text-red-600 hover:text-red-700 font-medium"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <p className="text-gray-600">No holdings yet. Add one above!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default PortfolioSimple
