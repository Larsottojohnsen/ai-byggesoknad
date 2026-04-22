'use client'

import { useState, useEffect, useRef } from 'react'
import { MapPin, Search, ChevronRight, Loader2 } from 'lucide-react'
import { searchAddress } from '@/lib/api'
import type { AddressSuggestion } from '@/types'
import type { WizardData } from '@/app/wizard/page'
import { WizardMap } from './WizardMap'

interface Props {
  data: WizardData
  onUpdate: (updates: Partial<WizardData>) => void
  onNext: () => void
}

export function WizardStep1Address({ data, onUpdate, onNext }: Props) {
  const [query, setQuery] = useState(data.address?.addressText ?? '')
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (query.length < 3) {
      setSuggestions([])
      return
    }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const results = await searchAddress(query)
        setSuggestions(results)
        setShowDropdown(true)
      } catch {
        setSuggestions([])
      } finally {
        setLoading(false)
      }
    }, 300)
  }, [query])

  function handleSelect(suggestion: AddressSuggestion) {
    onUpdate({ address: suggestion })
    setQuery(suggestion.addressText)
    setShowDropdown(false)
    setSuggestions([])
  }

  function handleClear() {
    onUpdate({ address: null })
    setQuery('')
    setSuggestions([])
    setShowDropdown(false)
    inputRef.current?.focus()
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Hvilken eiendom gjelder det?</h1>
        <p className="text-gray-500 mt-1">Søk opp adressen til eiendommen du vil bygge på.</p>
      </div>

      {/* Search field */}
      <div className="relative">
        <div className="flex items-center gap-3 bg-white border-2 border-gray-200 rounded-2xl px-4 py-3.5 focus-within:border-blue-500 transition-colors shadow-sm">
          {loading ? (
            <Loader2 className="w-5 h-5 text-blue-500 animate-spin flex-shrink-0" />
          ) : (
            <Search className="w-5 h-5 text-gray-400 flex-shrink-0" />
          )}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => {
              setQuery(e.target.value)
              if (data.address) onUpdate({ address: null })
            }}
            onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
            placeholder="F.eks. Storgata 1, Oslo"
            className="flex-1 outline-none text-gray-900 placeholder-gray-400 text-base bg-transparent"
            autoComplete="off"
          />
          {query && (
            <button
              onClick={handleClear}
              className="text-gray-400 hover:text-gray-600 text-lg leading-none flex-shrink-0"
            >
              ×
            </button>
          )}
        </div>

        {/* Dropdown */}
        {showDropdown && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 overflow-hidden">
            {suggestions.map(s => (
              <button
                key={s.id}
                onClick={() => handleSelect(s)}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-blue-50 text-left transition-colors border-b border-gray-50 last:border-0"
              >
                <MapPin className="w-4 h-4 text-blue-500 flex-shrink-0" />
                <div>
                  <div className="text-sm font-medium text-gray-900">{s.addressText}</div>
                  <div className="text-xs text-gray-500">{s.municipality}</div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Map preview */}
      {data.address && (
        <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 flex items-center gap-3">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
              <MapPin className="w-4 h-4 text-green-600" />
            </div>
            <div>
              <div className="font-semibold text-green-900 text-sm">{data.address.addressText}</div>
              <div className="text-xs text-green-700">{data.address.municipality} · {data.address.lat.toFixed(5)}, {data.address.lng.toFixed(5)}</div>
            </div>
          </div>

          <WizardMap
            lat={data.address.lat}
            lng={data.address.lng}
            className="h-56 rounded-2xl overflow-hidden border border-gray-200 shadow-sm"
          />
        </div>
      )}

      {/* Next button */}
      <button
        onClick={onNext}
        disabled={!data.address}
        className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold py-4 rounded-2xl transition-all text-base shadow-sm disabled:shadow-none"
      >
        Neste: Velg tiltak
        <ChevronRight className="w-5 h-5" />
      </button>

      {!data.address && (
        <p className="text-center text-xs text-gray-400">Søk opp og velg en adresse for å fortsette</p>
      )}
    </div>
  )
}
