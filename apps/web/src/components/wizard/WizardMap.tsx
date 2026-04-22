'use client'

import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'

interface WizardMapProps {
  lat: number
  lng: number
  zoom?: number
  className?: string
  showLayers?: boolean
  activeLayers?: Set<string>
}

// Kartverket WMTS works perfectly with EPSG:3857 (web mercator)
// For WMS overlays, we use the correct CRS per service:
// - wms.matrikkel: requires EPSG:25833 (UTM zone 33N)
// - wms.arealplaner2: supports EPSG:3857
// - NVE: supports EPSG:3857

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

export function WizardMap({
  lat,
  lng,
  zoom = 16,
  className,
  showLayers = false,
  activeLayers = new Set<string>(),
}: WizardMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<import('maplibre-gl').Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const markerRef = useRef<import('maplibre-gl').Marker | null>(null)

  useEffect(() => {
    if (!mapContainer.current) return
    let map: import('maplibre-gl').Map

    import('maplibre-gl').then(({ Map, Marker, NavigationControl }) => {
      map = new Map({
        container: mapContainer.current!,
        style: KARTVERKET_STYLE,
        center: [lng, lat],
        zoom,
        attributionControl: false,
      })

      map.addControl(new NavigationControl({ showCompass: false }), 'top-right')

      map.on('load', () => {
        setMapLoaded(true)

        // Add property marker
        const el = document.createElement('div')
        el.className = 'property-marker'
        el.style.cssText = `
          width: 32px; height: 32px;
          background: #2563eb;
          border: 3px solid white;
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          cursor: pointer;
        `
        markerRef.current = new Marker({ element: el, anchor: 'bottom' })
          .setLngLat([lng, lat])
          .addTo(map)

        // Add WMS layers if requested
        if (showLayers) {
          addWmsLayers(map, activeLayers)
        }
      })

      mapRef.current = map
    })

    return () => {
      if (markerRef.current) markerRef.current.remove()
      if (map) map.remove()
      mapRef.current = null
      setMapLoaded(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lng, zoom])

  // Update WMS layers when activeLayers changes
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || !showLayers) return
    const map = mapRef.current
    updateWmsLayers(map, activeLayers)
  }, [activeLayers, mapLoaded, showLayers])

  return (
    <div className={cn('relative', className)}>
      <div ref={mapContainer} className="w-full h-full" />
      <div className="absolute bottom-2 left-2 bg-white/80 backdrop-blur-sm text-xs text-gray-500 px-2 py-1 rounded-lg">
        © Kartverket
      </div>
    </div>
  )
}

// ── WMS layer helpers ─────────────────────────────────────────────────────────

const WMS_DEFS: Record<string, { url: string; opacity: number }> = {
  // Eiendomsgrenser — Norgeskart cache supports EPSG:3857
  matrikkel: {
    url: 'https://openwms.statkart.no/skwms1/wms.matrikkelkart?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=Eiendomsgrenser&STYLES=&FORMAT=image/png&TRANSPARENT=true&CRS=EPSG:3857&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256',
    opacity: 0.9,
  },
  // Reguleringsplan — arealformål via Geonorge
  arealplan: {
    url: 'https://openwms.statkart.no/skwms1/wms.arealplaner?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=arealformaal&STYLES=&FORMAT=image/png&TRANSPARENT=true&CRS=EPSG:3857&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256',
    opacity: 0.6,
  },
  // Flomsoner NVE — kart.nve.no
  flom: {
    url: 'https://kart.nve.no/enterprise/rest/services/Flomaktsomhet/MapServer/export?bbox={bbox-epsg-3857}&bboxSR=3857&size=256,256&imageSR=3857&format=png&transparent=true&f=image',
    opacity: 0.7,
  },
  // Skredfareområder NVE
  skred: {
    url: 'https://kart.nve.no/enterprise/rest/services/Skredfaresoner/MapServer/export?bbox={bbox-epsg-3857}&bboxSR=3857&size=256,256&imageSR=3857&format=png&transparent=true&f=image',
    opacity: 0.7,
  },
}

function addWmsLayers(map: import('maplibre-gl').Map, activeLayers: Set<string>) {
  Object.entries(WMS_DEFS).forEach(([id, def]) => {
    if (!map.getSource(`wms-${id}`)) {
      map.addSource(`wms-${id}`, {
        type: 'raster',
        tiles: [def.url],
        tileSize: 256,
      })
    }
    if (!map.getLayer(`wms-layer-${id}`)) {
      map.addLayer({
        id: `wms-layer-${id}`,
        type: 'raster',
        source: `wms-${id}`,
        paint: { 'raster-opacity': def.opacity },
        layout: { visibility: activeLayers.has(id) ? 'visible' : 'none' },
      })
    }
  })
}

function updateWmsLayers(map: import('maplibre-gl').Map, activeLayers: Set<string>) {
  Object.keys(WMS_DEFS).forEach(id => {
    const layerId = `wms-layer-${id}`
    if (!map.getLayer(layerId)) {
      // Add if not present
      if (!map.getSource(`wms-${id}`)) {
        map.addSource(`wms-${id}`, {
          type: 'raster',
          tiles: [WMS_DEFS[id].url],
          tileSize: 256,
        })
      }
      map.addLayer({
        id: layerId,
        type: 'raster',
        source: `wms-${id}`,
        paint: { 'raster-opacity': WMS_DEFS[id].opacity },
        layout: { visibility: activeLayers.has(id) ? 'visible' : 'none' },
      })
    } else {
      map.setLayoutProperty(layerId, 'visibility', activeLayers.has(id) ? 'visible' : 'none')
    }
  })
}
