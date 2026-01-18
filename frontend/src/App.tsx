import { useState, useEffect } from 'react'
import { ChatInterface } from './components/Chat/ChatInterface'
import { ConversationHistory } from './components/Chat/ConversationHistory'
import { PortfolioSimple } from './components/Portfolio/PortfolioSimple'
import { PortfolioAnalytics } from './components/Portfolio/PortfolioAnalytics'
import { TaxImpactAnalysis } from './components/Portfolio/TaxImpactAnalysis'
import { DividendAnalysis } from './components/Portfolio/DividendAnalysis'
import { SectorHeatmap } from './components/Portfolio/SectorHeatmap'
import { PortfolioAnalysisView } from './components/Portfolio/PortfolioAnalysisView'
import { MarketAnalysisView } from './components/Market/MarketAnalysisView'
import { GoalPlanningView } from './components/Goals/GoalPlanningView'
import LangGraphStateTab from './components/LangGraphStateTab'
import { useSettingsStore } from './store/settingsStore'
import { useChatStore } from './store/chatStore'
import './App.css'

type Tab = 'chat' | 'portfolio' | 'market' | 'goals' | 'history' | 'langgraph' | 'settings'
type PortfolioTab = 'input' | 'analytics' | 'tax' | 'dividend' | 'sector' | 'analysis'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat')
  const [portfolioTab, setPortfolioTab] = useState<PortfolioTab>('input')
  const { settings, loadSettings, updateName, updateRiskAppetite, updateInvestmentExperience, updateEmailNotifications, updateMarketAlerts, updateDarkMode, saveSettings } = useSettingsStore()
  const { messages, loading } = useChatStore()

  useEffect(() => {
    loadSettings()
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Finance Assistant</h1>
              <p className="text-sm text-gray-600 mt-1">Chat, Manage Portfolio, View History</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex gap-2 border-b border-gray-200 overflow-x-auto">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => setActiveTab('portfolio')}
              className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'portfolio'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              📊 Portfolio
            </button>
            <button
              onClick={() => setActiveTab('market')}
              className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'market'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              📈 Market
            </button>
            <button
              onClick={() => setActiveTab('goals')}
              className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'goals'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              🎯 Goals
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              📝 History
            </button>
            <button
              onClick={() => setActiveTab('langgraph')}
              className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'langgraph'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              ⚡ LangGraph State
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 whitespace-nowrap ${
                activeTab === 'settings'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              ⚙️ Settings
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {activeTab === 'chat' && <ChatInterface />}

        {activeTab === 'portfolio' && (
          <div>
            {/* Portfolio Sub-Tabs */}
            <div className="flex gap-2 mb-6 bg-white p-3 rounded-lg border border-gray-200 overflow-x-auto">
              <button
                onClick={() => setPortfolioTab('input')}
                className={`px-4 py-2 font-medium text-sm rounded transition-colors whitespace-nowrap ${
                  portfolioTab === 'input'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                ➕ Add Holdings
              </button>
              <button
                onClick={() => setPortfolioTab('analytics')}
                className={`px-4 py-2 font-medium text-sm rounded transition-colors whitespace-nowrap ${
                  portfolioTab === 'analytics'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                📊 Analytics
              </button>
              <button
                onClick={() => setPortfolioTab('tax')}
                className={`px-4 py-2 font-medium text-sm rounded transition-colors whitespace-nowrap ${
                  portfolioTab === 'tax'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                💰 Tax Impact
              </button>
              <button
                onClick={() => setPortfolioTab('dividend')}
                className={`px-4 py-2 font-medium text-sm rounded transition-colors whitespace-nowrap ${
                  portfolioTab === 'dividend'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                💵 Dividends
              </button>
              <button
                onClick={() => setPortfolioTab('analysis')}
                className={`px-4 py-2 font-medium text-sm rounded transition-colors whitespace-nowrap ${
                  portfolioTab === 'analysis'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                🤖 AI Analysis
              </button>
            </div>

            {/* Portfolio Content */}
            {portfolioTab === 'input' && <PortfolioSimple />}
            {portfolioTab === 'analytics' && <PortfolioAnalytics />}
            {portfolioTab === 'analysis' && <PortfolioAnalysisView />}
            {portfolioTab === 'tax' && <TaxImpactAnalysis />}
            {portfolioTab === 'dividend' && <DividendAnalysis />}
            {portfolioTab === 'sector' && <SectorHeatmap />}
          </div>
        )}

        {activeTab === 'market' && <MarketAnalysisView />}
        {activeTab === 'goals' && <GoalPlanningView />}
        {activeTab === 'history' && <ConversationHistory />}
        {activeTab === 'langgraph' && <LangGraphStateTab messages={messages} loading={loading} />}

        {activeTab === 'settings' && (
          <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Settings</h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">User Profile</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Name
                    </label>
                    <input
                      type="text"
                      value={settings.name}
                      onChange={(e) => updateName(e.target.value)}
                      placeholder="Your name"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Risk Appetite
                    </label>
                    <select 
                      value={settings.riskAppetite}
                      onChange={(e) => updateRiskAppetite(e.target.value as 'low' | 'moderate' | 'high')}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="low">Low (Conservative)</option>
                      <option value="moderate">Moderate (Balanced)</option>
                      <option value="high">High (Aggressive)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Investment Experience
                    </label>
                    <select 
                      value={settings.investmentExperience}
                      onChange={(e) => updateInvestmentExperience(e.target.value as 'beginner' | 'intermediate' | 'advanced')}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Preferences</h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={settings.emailNotifications}
                      onChange={(e) => updateEmailNotifications(e.target.checked)}
                      className="w-4 h-4 text-blue-600" 
                    />
                    <span className="text-gray-700">Email notifications</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={settings.marketAlerts}
                      onChange={(e) => updateMarketAlerts(e.target.checked)}
                      className="w-4 h-4 text-blue-600" 
                    />
                    <span className="text-gray-700">Market alerts</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={settings.darkMode}
                      onChange={(e) => updateDarkMode(e.target.checked)}
                      className="w-4 h-4 text-blue-600" 
                    />
                    <span className="text-gray-700">Dark mode</span>
                  </label>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <button 
                  onClick={() => saveSettings(settings)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Save Settings
                </button>
                <p className="text-sm text-green-600 mt-2">✓ Settings auto-saved</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
export default App
