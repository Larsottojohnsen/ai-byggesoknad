'use client'

import { ChevronRight, ChevronLeft } from 'lucide-react'
import type { MeasureType } from '@/types'
import type { WizardData } from '@/app/wizard/page'
import { cn } from '@/lib/utils'

interface Props {
  data: WizardData
  onUpdate: (updates: Partial<WizardData>) => void
  onNext: () => void
  onBack: () => void
}

const MEASURES: {
  type: MeasureType
  label: string
  description: string
  icon: string
  popular?: boolean
}[] = [
  {
    type: 'garasje',
    label: 'Garasje / carport',
    description: 'Frittliggende garasje, carport eller uthus',
    icon: '🚗',
    popular: true,
  },
  {
    type: 'tilbygg',
    label: 'Tilbygg',
    description: 'Utvide boligen med nytt rom eller areal',
    icon: '🏗️',
    popular: true,
  },
  {
    type: 'veranda',
    label: 'Terrasse / veranda',
    description: 'Ny terrasse, veranda eller balkong',
    icon: '🌿',
    popular: true,
  },
  {
    type: 'bruksendring',
    label: 'Bruksendring',
    description: 'Endre bruk av rom, f.eks. kjeller til bolig',
    icon: '🔄',
  },
  {
    type: 'kjeller_innredning',
    label: 'Kjeller / loft',
    description: 'Innrede kjeller eller loft til boligformål',
    icon: '🏠',
  },
  {
    type: 'fasadeendring',
    label: 'Fasadeendring',
    description: 'Endre utseende på bygning, nye vinduer/dører',
    icon: '🎨',
  },
  {
    type: 'støttemur',
    label: 'Støttemur / gjerde',
    description: 'Sette opp gjerde, støttemur eller mur',
    icon: '🧱',
  },
  {
    type: 'påbygg',
    label: 'Påbygg',
    description: 'Bygge på toppen av eksisterende bygg',
    icon: '⬆️',
  },
  {
    type: 'annet',
    label: 'Annet',
    description: 'Noe annet — beskriv selv',
    icon: '📋',
  },
]

export function WizardStep2Measure({ data, onUpdate, onNext, onBack }: Props) {
  function handleSelect(type: MeasureType, label: string) {
    onUpdate({ measureType: type, measureLabel: label })
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <button
          onClick={onBack}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          {data.address?.municipality ?? 'Tilbake'}
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Hva vil du bygge?</h1>
        <p className="text-gray-500 mt-1">Velg tiltakstype for å få riktig vurdering.</p>
      </div>

      {/* Popular */}
      <div>
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Mest vanlig</div>
        <div className="grid grid-cols-3 gap-3">
          {MEASURES.filter(m => m.popular).map(m => (
            <button
              key={m.type}
              onClick={() => handleSelect(m.type, m.label)}
              className={cn(
                'flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all text-center',
                data.measureType === m.type
                  ? 'border-blue-500 bg-blue-50 shadow-sm'
                  : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/50'
              )}
            >
              <span className="text-3xl">{m.icon}</span>
              <span className="text-sm font-semibold text-gray-900 leading-tight">{m.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* All options */}
      <div>
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Alle tiltakstyper</div>
        <div className="space-y-2">
          {MEASURES.filter(m => !m.popular).map(m => (
            <button
              key={m.type}
              onClick={() => handleSelect(m.type, m.label)}
              className={cn(
                'w-full flex items-center gap-4 p-4 rounded-2xl border-2 transition-all text-left',
                data.measureType === m.type
                  ? 'border-blue-500 bg-blue-50 shadow-sm'
                  : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/50'
              )}
            >
              <span className="text-2xl flex-shrink-0">{m.icon}</span>
              <div>
                <div className="font-semibold text-gray-900 text-sm">{m.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{m.description}</div>
              </div>
              {data.measureType === m.type && (
                <div className="ml-auto w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xs">✓</span>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Next button */}
      <button
        onClick={onNext}
        disabled={!data.measureType}
        className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold py-4 rounded-2xl transition-all text-base shadow-sm disabled:shadow-none"
      >
        Neste: Få vurdering
        <ChevronRight className="w-5 h-5" />
      </button>
    </div>
  )
}
