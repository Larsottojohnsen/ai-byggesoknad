'use client'

import { useEffect, useRef, useState } from 'react'
import { useProjectStore } from '@/store/projectStore'
import { Layers } from 'lucide-react'
import { cn } from '@/lib/utils'

// MapLibre is loaded dynamically to avoid SSR issues
let maplibregl: typeof import('maplibre-gl') | null = null

const KARTVERKET_STYLE = {
  version: 8 as const,
  sources: {
    kartverket: {
      type: 'raster' as const,
      tiles: [
        'https://cache.kartverket.no/v1/wmts/1.0.0/topo/default/webmercator/{z}/{y}/{x}.png',
      ],
      tileSize: 256,
      attribution: '© Kartverket',
    },
  },
  layers: [
    {
      id: 'kartverket-tiles',
      type: 'raster' as const,
      source: 'kartverket',
    },
  ],
}

interface MapViewProps {
  className?: string
}

export function MapView({ className }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<import('maplibre-gl').Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [showLayers, setShowLayers] = useState(false)

  const {
    mapCenter,
    mapZoom,
    activeLayers,
    toggleLayer,
    analysisResult,
    selectedAddress,
  } = useProjectStore()

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return

    async function initMap() {
      const ml = await import('maplibre-gl')
      await import('maplibre-gl/dist/maplibre-gl.css')
      maplibregl = ml

      const map = new ml.Map({
        container: mapContainer.current!,
        style: KARTVERKET_STYLE,
        center: mapCenter,
        zoom: mapZoom,
        attributionControl: true,
      })

      map.on('load', () => {
        setMapLoaded(true)
      })

      mapRef.current = map
    }

    initMap()

    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Fly to address when selected
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || !selectedAddress) return
    mapRef.current.flyTo({
      center: [selectedAddress.lng, selectedAddress.lat],
      zoom: 15,
      duration: 1500,
    })
  }, [selectedAddress, mapLoaded])

  // Add property geometry layer when analysis result arrives
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || !analysisResult?.property?.geometry) return

    const map = mapRef.current
    const geom = analysisResult.property.geometry

    // Remove existing layers
    if (map.getLayer('property-fill')) map.removeLayer('property-fill')
    if (map.getLayer('property-outline')) map.removeLayer('property-outline')
    if (map.getSource('property')) map.removeSource('property')

    map.addSource('property', {
      type: 'geojson',
      data: geom as GeoJSON.Feature,
    })

    map.addLayer({
      id: 'property-fill',
      type: 'fill',
      source: 'property',
      paint: {
        'fill-color': '#3b82f6',
        'fill-opacity': 0.15,
      },
    })

    map.addLayer({
      id: 'property-outline',
      type: 'line',
      source: 'property',
      paint: {
        'line-color': '#2563eb',
        'line-width': 2,
      },
    })
  }, [analysisResult, mapLoaded])

  // Toggle layer visibility
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return
    const map = mapRef.current

    const layerIds = ['property-fill', 'property-outline']
    layerIds.forEach((id) => {
      if (map.getLayer(id)) {
        map.setLayoutProperty(
          id,
          'visibility',
          activeLayers.includes('property') ? 'visible' : 'none'
        )
      }
    })
  }, [activeLayers, mapLoaded])

  const LAYER_OPTIONS = [
    { id: 'property', label: 'Eiendomsgrenser' },
    { id: 'plan', label: 'Reguleringsplan' },
    { id: 'hazard', label: 'Faredata' },
  ]

  return (
    <div className={cn('relative rounded-xl overflow-hidden border border-gray-200', className)}>
      <div ref={mapContainer} className="w-full h-full" />

      {/* Layer toggle */}
      <div className="absolute top-3 right-3 z-10">
        <button
          onClick={() => setShowLayers(!showLayers)}
          className="bg-white shadow-md rounded-lg p-2 hover:bg-gray-50 transition-colors"
          title="Kartlag"
        >
          <Layers className="w-5 h-5 text-gray-700" />
        </button>

        {showLayers && (
          <div className="absolute top-full right-0 mt-1 bg-white shadow-lg rounded-lg border border-gray-200 p-3 min-w-[180px]">
            <div className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">
              Kartlag
            </div>
            {LAYER_OPTIONS.map((layer) => (
              <label
                key={layer.id}
                className="flex items-center gap-2 py-1 cursor-pointer hover:text-blue-600"
              >
                <input
                  type="checkbox"
                  checked={activeLayers.includes(layer.id)}
                  onChange={() => toggleLayer(layer.id)}
                  className="rounded border-gray-300 text-blue-600"
                />
                <span className="text-sm text-gray-700">{layer.label}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Address marker */}
      {selectedAddress && mapLoaded && (
        <div className="absolute bottom-3 left-3 bg-white shadow-md rounded-lg px-3 py-2 text-xs text-gray-700 max-w-[200px] truncate">
          📍 {selectedAddress.addressText}
        </div>
      )}
    </div>
  )
}
