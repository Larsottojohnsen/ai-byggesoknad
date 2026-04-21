'use client'

import { useEffect, useRef, useState } from 'react'
import { useProjectStore } from '@/store/projectStore'
import { Layers } from 'lucide-react'
import { cn } from '@/lib/utils'

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

// WMS overlay definitions
const WMS_LAYERS = [
  {
    id: 'matrikkel',
    label: 'Eiendomsgrenser',
    color: '#2563eb',
    url: 'https://wms.geonorge.no/skwms1/wms.matrikkel?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=Eiendomsgrenser&STYLES=&FORMAT=image/png&TRANSPARENT=true&CRS=EPSG:3857&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256',
  },
  {
    id: 'arealplan',
    label: 'Reguleringsplan',
    color: '#16a34a',
    url: 'https://openwms.statkart.no/skwms1/wms.arealplaner2?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=arealformaal&STYLES=&FORMAT=image/png&TRANSPARENT=true&CRS=EPSG:3857&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256',
  },
  {
    id: 'flom',
    label: 'Flomsoner (NVE)',
    color: '#0ea5e9',
    url: 'https://nve.geodataonline.no/arcgis/services/Mapservices/FlomAktsomhet/MapServer/WMSServer?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=0&STYLES=&FORMAT=image/png&TRANSPARENT=true&CRS=EPSG:3857&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256',
  },
  {
    id: 'skred',
    label: 'Skredfareområder (NVE)',
    color: '#dc2626',
    url: 'https://nve.geodataonline.no/arcgis/services/Mapservices/SkredAktsomhet/MapServer/WMSServer?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=0&STYLES=&FORMAT=image/png&TRANSPARENT=true&CRS=EPSG:3857&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256',
  },
]

interface MapViewProps {
  className?: string
}

export function MapView({ className }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<import('maplibre-gl').Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [showLayers, setShowLayers] = useState(false)
  const [activeWmsLayers, setActiveWmsLayers] = useState<Set<string>>(
    new Set(['matrikkel'])
  )

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

      const map = new ml.Map({
        container: mapContainer.current!,
        style: KARTVERKET_STYLE,
        center: mapCenter,
        zoom: mapZoom,
        attributionControl: true,
      })

      map.on('load', () => {
        // Add WMS overlay sources
        WMS_LAYERS.forEach(layer => {
          map.addSource(`wms-${layer.id}`, {
            type: 'raster',
            tiles: [layer.url],
            tileSize: 256,
          })
          map.addLayer({
            id: `wms-${layer.id}`,
            type: 'raster',
            source: `wms-${layer.id}`,
            paint: { 'raster-opacity': 0.65 },
            layout: {
              visibility: layer.id === 'matrikkel' ? 'visible' : 'none',
            },
          })
        })

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
      zoom: 16,
      duration: 1500,
    })
  }, [selectedAddress, mapLoaded])

  // Add property geometry layer when analysis result arrives
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return
    const map = mapRef.current

    // Remove existing GeoJSON layers
    ;['property-fill', 'property-outline', 'property-circle'].forEach(id => {
      if (map.getLayer(id)) map.removeLayer(id)
    })
    if (map.getSource('property')) map.removeSource('property')

    if (analysisResult?.property?.geometry) {
      const geom = analysisResult.property.geometry
      map.addSource('property', {
        type: 'geojson',
        data: geom as GeoJSON.Feature,
      })
      map.addLayer({
        id: 'property-fill',
        type: 'fill',
        source: 'property',
        paint: { 'fill-color': '#3b82f6', 'fill-opacity': 0.12 },
      })
      map.addLayer({
        id: 'property-outline',
        type: 'line',
        source: 'property',
        paint: { 'line-color': '#2563eb', 'line-width': 2.5 },
      })
    } else if (selectedAddress) {
      // Draw approximate circle when no geometry available
      const { lat, lng } = selectedAddress
      const coords = buildCircle(lat, lng, 40)
      map.addSource('property', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: { type: 'Polygon', coordinates: [coords] },
          properties: {},
        } as GeoJSON.Feature,
      })
      map.addLayer({
        id: 'property-fill',
        type: 'fill',
        source: 'property',
        paint: { 'fill-color': '#3b82f6', 'fill-opacity': 0.1 },
      })
      map.addLayer({
        id: 'property-outline',
        type: 'line',
        source: 'property',
        paint: {
          'line-color': '#2563eb',
          'line-width': 2,
          'line-dasharray': [4, 2],
        },
      })
    }
  }, [analysisResult, selectedAddress, mapLoaded])

  // Toggle WMS layer visibility
  const toggleWmsLayer = (layerId: string) => {
    if (!mapRef.current || !mapLoaded) return
    const map = mapRef.current
    const next = new Set(activeWmsLayers)
    const isVisible = next.has(layerId)

    if (isVisible) {
      next.delete(layerId)
    } else {
      next.add(layerId)
    }
    setActiveWmsLayers(next)

    const mapLayerId = `wms-${layerId}`
    if (map.getLayer(mapLayerId)) {
      map.setLayoutProperty(mapLayerId, 'visibility', isVisible ? 'none' : 'visible')
    }
  }

  return (
    <div className={cn('relative rounded-xl overflow-hidden border border-gray-200', className)}>
      <div ref={mapContainer} className="w-full h-full" />

      {/* Layer toggle */}
      <div className="absolute top-3 right-3 z-10">
        <button
          onClick={() => setShowLayers(!showLayers)}
          className="bg-white shadow-md rounded-lg p-2 hover:bg-gray-50 transition-colors border border-gray-200"
          title="Kartlag"
        >
          <Layers className="w-5 h-5 text-gray-700" />
        </button>

        {showLayers && (
          <div className="absolute top-full right-0 mt-1 bg-white shadow-lg rounded-lg border border-gray-200 p-3 min-w-[210px]">
            <div className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
              Kartlag
            </div>
            {WMS_LAYERS.map(layer => (
              <label
                key={layer.id}
                className="flex items-center gap-2 py-1.5 cursor-pointer hover:text-blue-600 group"
              >
                <input
                  type="checkbox"
                  checked={activeWmsLayers.has(layer.id)}
                  onChange={() => toggleWmsLayer(layer.id)}
                  className="rounded border-gray-300 text-blue-600"
                />
                <span
                  className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                  style={{ backgroundColor: layer.color }}
                />
                <span className="text-sm text-gray-700 group-hover:text-blue-600">
                  {layer.label}
                </span>
              </label>
            ))}
            <div className="border-t border-gray-100 mt-2 pt-2">
              <p className="text-xs text-gray-400">
                Kart: © Kartverket · NVE
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Risk level badge */}
      {analysisResult?.riskLevel && (
        <div className="absolute bottom-10 left-3 z-10">
          <span
            className={cn(
              'px-3 py-1.5 rounded-full text-xs font-bold shadow-md border',
              analysisResult.riskLevel === 'høy'
                ? 'bg-red-100 text-red-700 border-red-200'
                : analysisResult.riskLevel === 'middels'
                ? 'bg-amber-100 text-amber-700 border-amber-200'
                : 'bg-green-100 text-green-700 border-green-200'
            )}
          >
            {analysisResult.riskLevel === 'høy' ? '🔴' : analysisResult.riskLevel === 'middels' ? '🟡' : '🟢'}{' '}
            Risiko: {analysisResult.riskLevel}
          </span>
        </div>
      )}

      {/* Address label */}
      {selectedAddress && mapLoaded && (
        <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm shadow-md rounded-lg px-3 py-1.5 text-xs text-gray-700 max-w-[240px] truncate border border-gray-200">
          📍 {selectedAddress.addressText}
        </div>
      )}
    </div>
  )
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function buildCircle(lat: number, lng: number, radiusMeters: number): [number, number][] {
  const points = 48
  const earthRadius = 6371000
  const coords: [number, number][] = []
  for (let i = 0; i <= points; i++) {
    const angle = (i / points) * 2 * Math.PI
    const dx = (radiusMeters * Math.cos(angle)) / earthRadius
    const dy = (radiusMeters * Math.sin(angle)) / earthRadius
    coords.push([
      lng + (dx * 180) / Math.PI / Math.cos((lat * Math.PI) / 180),
      lat + (dy * 180) / Math.PI,
    ])
  }
  return coords
}
