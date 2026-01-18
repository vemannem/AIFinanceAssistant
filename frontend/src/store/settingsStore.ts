import { create } from 'zustand'

export interface UserSettings {
  name: string
  riskAppetite: 'low' | 'moderate' | 'high'
  investmentExperience: 'beginner' | 'intermediate' | 'advanced'
  emailNotifications: boolean
  marketAlerts: boolean
  darkMode: boolean
}

const defaultSettings: UserSettings = {
  name: 'Investor',
  riskAppetite: 'moderate',
  investmentExperience: 'beginner',
  emailNotifications: true,
  marketAlerts: true,
  darkMode: false,
}

interface SettingsStore {
  settings: UserSettings
  loadSettings: () => void
  saveSettings: (settings: UserSettings) => void
  updateName: (name: string) => void
  updateRiskAppetite: (risk: 'low' | 'moderate' | 'high') => void
  updateInvestmentExperience: (exp: 'beginner' | 'intermediate' | 'advanced') => void
  updateEmailNotifications: (enabled: boolean) => void
  updateMarketAlerts: (enabled: boolean) => void
  updateDarkMode: (enabled: boolean) => void
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: defaultSettings,

  loadSettings: () => {
    try {
      const stored = localStorage.getItem('userSettings')
      if (stored) {
        const parsed = JSON.parse(stored)
        set({ settings: { ...defaultSettings, ...parsed } })
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  },

  saveSettings: (settings: UserSettings) => {
    try {
      localStorage.setItem('userSettings', JSON.stringify(settings))
      set({ settings })
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
  },

  updateName: (name: string) => {
    set((state) => {
      const updated = { ...state.settings, name }
      localStorage.setItem('userSettings', JSON.stringify(updated))
      return { settings: updated }
    })
  },

  updateRiskAppetite: (risk: 'low' | 'moderate' | 'high') => {
    set((state) => {
      const updated = { ...state.settings, riskAppetite: risk }
      localStorage.setItem('userSettings', JSON.stringify(updated))
      return { settings: updated }
    })
  },

  updateInvestmentExperience: (exp: 'beginner' | 'intermediate' | 'advanced') => {
    set((state) => {
      const updated = { ...state.settings, investmentExperience: exp }
      localStorage.setItem('userSettings', JSON.stringify(updated))
      return { settings: updated }
    })
  },

  updateEmailNotifications: (enabled: boolean) => {
    set((state) => {
      const updated = { ...state.settings, emailNotifications: enabled }
      localStorage.setItem('userSettings', JSON.stringify(updated))
      return { settings: updated }
    })
  },

  updateMarketAlerts: (enabled: boolean) => {
    set((state) => {
      const updated = { ...state.settings, marketAlerts: enabled }
      localStorage.setItem('userSettings', JSON.stringify(updated))
      return { settings: updated }
    })
  },

  updateDarkMode: (enabled: boolean) => {
    set((state) => {
      const updated = { ...state.settings, darkMode: enabled }
      localStorage.setItem('userSettings', JSON.stringify(updated))
      return { settings: updated }
    })
  },
}))
