import { create } from 'zustand'
import type { AddressSuggestion, AnalysisResult, Project } from '@/types'

interface ProjectStore {
  // Selected address
  selectedAddress: AddressSuggestion | null
  setSelectedAddress: (address: AddressSuggestion | null) => void

  // Intent text
  intentText: string
  setIntentText: (text: string) => void

  // Current project
  currentProject: Project | null
  setCurrentProject: (project: Project | null) => void

  // Analysis result
  analysisResult: AnalysisResult | null
  setAnalysisResult: (result: AnalysisResult | null) => void

  // Loading states
  isAnalyzing: boolean
  setIsAnalyzing: (loading: boolean) => void

  // Map state
  mapCenter: [number, number]
  mapZoom: number
  setMapCenter: (center: [number, number]) => void
  setMapZoom: (zoom: number) => void

  // Active map layers
  activeLayers: string[]
  toggleLayer: (layerId: string) => void

  // Reset
  reset: () => void
}

const DEFAULT_MAP_CENTER: [number, number] = [10.7522, 59.9139] // Oslo

export const useProjectStore = create<ProjectStore>((set) => ({
  selectedAddress: null,
  setSelectedAddress: (address) => set({ selectedAddress: address }),

  intentText: '',
  setIntentText: (text) => set({ intentText: text }),

  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),

  analysisResult: null,
  setAnalysisResult: (result) => set({ analysisResult: result }),

  isAnalyzing: false,
  setIsAnalyzing: (loading) => set({ isAnalyzing: loading }),

  mapCenter: DEFAULT_MAP_CENTER,
  mapZoom: 5,
  setMapCenter: (center) => set({ mapCenter: center }),
  setMapZoom: (zoom) => set({ mapZoom: zoom }),

  activeLayers: ['property', 'plan'],
  toggleLayer: (layerId) =>
    set((state) => ({
      activeLayers: state.activeLayers.includes(layerId)
        ? state.activeLayers.filter((id) => id !== layerId)
        : [...state.activeLayers, layerId],
    })),

  reset: () =>
    set({
      selectedAddress: null,
      intentText: '',
      currentProject: null,
      analysisResult: null,
      isAnalyzing: false,
      mapCenter: DEFAULT_MAP_CENTER,
      mapZoom: 5,
      activeLayers: ['property', 'plan'],
    }),
}))
