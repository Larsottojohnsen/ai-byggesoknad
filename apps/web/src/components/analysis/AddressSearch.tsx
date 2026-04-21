'use client'

import { useState, useEffect, useRef } from 'react'
import { MapPin, Loader2, Search } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { searchAddress } from '@/lib/api'
import type { AddressSuggestion } from '@/types'
import { cn } from '@/lib/utils'

interface AddressSearchProps {
  onSelect: (address: AddressSuggestion) => void
  value?: AddressSuggestion | null
  placeholder?: string
  className?: string
}

export function AddressSearch({
  onSelect,
  value,
  placeholder = 'Skriv inn adresse...',
  className,
}: AddressSearchProps) {
  const [query, setQuery] = useState(value?.addressText ?? '')
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const { data: suggestions = [], isFetching } = useQuery({
    queryKey: ['address-search', query],
    queryFn: () => searchAddress(query),
    enabled: query.length >= 3,
    staleTime: 30_000,
  })

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleSelect(suggestion: AddressSuggestion) {
    setQuery(suggestion.addressText)
    setOpen(false)
    onSelect(suggestion)
  }

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
          }}
          onFocus={() => query.length >= 3 && setOpen(true)}
          placeholder={placeholder}
          className="w-full pl-10 pr-10 py-3 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-base"
        />
        {isFetching && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
        )}
      </div>

      {open && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 overflow-hidden">
          {suggestions.map((s) => (
            <button
              key={s.id}
              onClick={() => handleSelect(s)}
              className="w-full flex items-start gap-3 px-4 py-3 hover:bg-blue-50 transition-colors text-left group"
            >
              <MapPin className="w-4 h-4 text-gray-400 group-hover:text-blue-500 mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-sm font-medium text-gray-900">{s.addressText}</div>
                <div className="text-xs text-gray-500">
                  {s.municipality}
                  {s.postalCode && `, ${s.postalCode} ${s.postalPlace ?? ''}`}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {open && query.length >= 3 && !isFetching && suggestions.length === 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 p-4 text-sm text-gray-500 text-center">
          Ingen adresser funnet for &quot;{query}&quot;
        </div>
      )}
    </div>
  )
}
