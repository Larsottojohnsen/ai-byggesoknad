'use client'

import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, Loader2, MapPin, ExternalLink, CheckCircle, XCircle, HelpCircle, AlertTriangle } from 'lucide-react'
import type { WizardData } from '@/app/wizard/page'
import type { AnalysisResult } from '@/types'
import { createProject, analyzeProject } from '@/lib/api'
import { WizardMap } from './WizardMap'
import { cn } from '@/lib/utils'

interface Props {
  data: WizardData
  onUpdate: (updates: Partial<WizardData>) => void
  onNext: () => void
  onBack: () => void
}

type LoadingStage = 'creating' | 'fetching_property' | 'fetching_plan' | 'fetching_hazard' | 'running_rules' | 'done' | 'error'

const LOADING_MESSAGES: Record<LoadingStage, string> = {
  creating: 'Oppretter prosjekt...',
  fetching_property: 'Henter eiendomsdata fra Kartverket...',
  fetching_plan: 'Sjekker reguleringsplan...',
  fetching_hazard: 'Sjekker faredata (NVE)...',
  running_rules: 'Vurderer søknadsplikt og regler...',
  done: 'Ferdig!',
  error: 'Noe gikk galt',
}

const STAGE_ORDER: LoadingStage[] = [
  'creating',
  'fetching_property',
  'fetching_plan',
  'fetching_hazard',
  'running_rules',
  'done',
]

export function WizardStep3Results({ data, onUpdate, onNext, onBack }: Props) {
  const [loadingStage, setLoadingStage] = useState<LoadingStage | null>(null)
  const [activeMapLayers, setActiveMapLayers] = useState<Set<string>>(new Set(['matrikkel', 'arealplan']))
  const [error, setError] = useState<string | null>(null)

  // Auto-run analysis when entering this step
  useEffect(() => {
    if (data.analysisResult) return // already have results
    if (!data.address || !data.measureType) return
    runAnalysis()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function runAnalysis() {
    setError(null)
    setLoadingStage('creating')

    try {
      // Simulate stage progression
      const stageTimer = (stage: LoadingStage, delay: number) =>
        new Promise<void>(resolve => setTimeout(() => { setLoadingStage(stage); resolve() }, delay))

      const project = await createProject({
        addressText: data.address!.addressText,
        lat: data.address!.lat,
        lng: data.address!.lng,
        intentText: `${data.measureLabel}: ${data.measureType}`,
      })
      onUpdate({ projectId: project.id })

      await stageTimer('fetching_property', 400)
      await stageTimer('fetching_plan', 800)
      await stageTimer('fetching_hazard', 1200)
      await stageTimer('running_rules', 1600)

      const result = await analyzeProject(project.id)
      onUpdate({ analysisResult: result })
      setLoadingStage('done')
    } catch (err) {
      console.error(err)
      setError('Kunne ikke hente vurdering. Sjekk at backend kjører.')
      setLoadingStage('error')
    }
  }

  function toggleLayer(id: string) {
    setActiveMapLayers(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const result = data.analysisResult
  const isLoading = loadingStage !== null && loadingStage !== 'done' && loadingStage !== 'error'

  // ── Loading state ─────────────────────────────────────────────────────────
  if (isLoading || loadingStage === null) {
    return (
      <div className="space-y-6">
        <div>
          <button onClick={onBack} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3">
            <ChevronLeft className="w-4 h-4" /> Tilbake
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Henter vurdering...</h1>
          <p className="text-gray-500 mt-1">Vi sjekker reguleringsplan, eiendomsdata og faredata.</p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
          {STAGE_ORDER.filter(s => s !== 'done').map((stage, i) => {
            const currentIdx = STAGE_ORDER.indexOf(loadingStage ?? 'creating')
            const stageIdx = i
            const isDone = stageIdx < currentIdx
            const isCurrent = stageIdx === currentIdx
            return (
              <div key={stage} className="flex items-center gap-3">
                <div className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition-all',
                  isDone ? 'bg-green-500' : isCurrent ? 'bg-blue-500' : 'bg-gray-100'
                )}>
                  {isDone ? (
                    <span className="text-white text-xs">✓</span>
                  ) : isCurrent ? (
                    <Loader2 className="w-3 h-3 text-white animate-spin" />
                  ) : (
                    <span className="text-gray-300 text-xs">{i + 1}</span>
                  )}
                </div>
                <span className={cn(
                  'text-sm transition-all',
                  isDone ? 'text-green-700 font-medium' : isCurrent ? 'text-blue-700 font-semibold' : 'text-gray-400'
                )}>
                  {LOADING_MESSAGES[stage]}
                </span>
              </div>
            )
          })}
        </div>

        {/* Map preview while loading */}
        {data.address && (
          <WizardMap
            lat={data.address.lat}
            lng={data.address.lng}
            className="h-48 rounded-2xl overflow-hidden border border-gray-200"
          />
        )}
      </div>
    )
  }

  // ── Error state ───────────────────────────────────────────────────────────
  if (error || loadingStage === 'error') {
    return (
      <div className="space-y-6">
        <div>
          <button onClick={onBack} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3">
            <ChevronLeft className="w-4 h-4" /> Tilbake
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Noe gikk galt</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-2xl p-5">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
        <button
          onClick={runAnalysis}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 rounded-2xl transition-all"
        >
          Prøv igjen
        </button>
      </div>
    )
  }

  if (!result) return null

  // ── Results ───────────────────────────────────────────────────────────────
  const permitStatus = result.applicationRequired === true
    ? 'required'
    : result.applicationRequired === false
    ? 'not_required'
    : 'uncertain'

  const blockingRules = result.ruleResults.filter(r => r.blocking && r.status === 'fail')
  const warnRules = result.ruleResults.filter(r => r.status === 'warn')

  return (
    <div className="space-y-5">
      {/* Back */}
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors">
        <ChevronLeft className="w-4 h-4" />
        {data.measureLabel} · {data.address?.municipality}
      </button>

      {/* ── Section A: Søknadsplikt ─────────────────────────────────────── */}
      <div className={cn(
        'rounded-2xl p-5 border-2',
        permitStatus === 'required' ? 'bg-amber-50 border-amber-300' :
        permitStatus === 'not_required' ? 'bg-green-50 border-green-300' :
        'bg-gray-50 border-gray-300'
      )}>
        <div className="flex items-start gap-4">
          <div className={cn(
            'w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0',
            permitStatus === 'required' ? 'bg-amber-100' :
            permitStatus === 'not_required' ? 'bg-green-100' :
            'bg-gray-100'
          )}>
            {permitStatus === 'required' ? (
              <AlertTriangle className="w-6 h-6 text-amber-600" />
            ) : permitStatus === 'not_required' ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <HelpCircle className="w-6 h-6 text-gray-500" />
            )}
          </div>
          <div className="flex-1">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">
              Trenger du å søke?
            </div>
            <div className={cn(
              'text-xl font-bold mb-2',
              permitStatus === 'required' ? 'text-amber-900' :
              permitStatus === 'not_required' ? 'text-green-900' :
              'text-gray-900'
            )}>
              {permitStatus === 'required' ? 'Ja — søknadspliktig' :
               permitStatus === 'not_required' ? 'Trolig ikke søknadspliktig' :
               'Usikker — krever vurdering'}
            </div>
            {result.aiSummary && (
              <p className="text-sm text-gray-700 leading-relaxed">{result.aiSummary}</p>
            )}
          </div>
        </div>

        {/* Blocking rules */}
        {blockingRules.length > 0 && (
          <div className="mt-4 space-y-2">
            {blockingRules.map(r => (
              <div key={r.ruleCode} className="flex items-start gap-2 bg-white/70 rounded-xl p-3">
                <XCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-semibold text-gray-900">{r.ruleName}</div>
                  <div className="text-xs text-gray-600 mt-0.5">{r.explanation}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Warning rules */}
        {warnRules.length > 0 && (
          <div className="mt-3 space-y-2">
            {warnRules.map(r => (
              <div key={r.ruleCode} className="flex items-start gap-2 bg-white/70 rounded-xl p-3">
                <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-semibold text-gray-900">{r.ruleName}</div>
                  <div className="text-xs text-gray-600 mt-0.5">{r.explanation}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Section B: Reguleringsplan ──────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <div className="px-5 pt-5 pb-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">
            Reguleringsplan og kart
          </div>
          <div className="text-base font-bold text-gray-900">
            {result.planLayer?.planName ?? result.planLayer?.planStatus ?? 'Plandata ikke tilgjengelig'}
          </div>
          {result.planLayer && (
            <div className="flex flex-wrap gap-2 mt-2">
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-medium capitalize">
                {result.planLayer.arealFormål}
              </span>
              {result.planLayer.utnyttelsesgrad && (
                <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full font-medium">
                  {result.planLayer.utnyttelsesgrad}
                </span>
              )}
              {result.planLayer.byggegrense && (
                <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full font-medium">
                  Byggegrense {result.planLayer.byggegrense} m
                </span>
              )}
            </div>
          )}
        </div>

        {/* Layer toggles */}
        <div className="px-5 pb-3 flex flex-wrap gap-2">
          {[
            { id: 'matrikkel', label: 'Eiendomsgrenser', color: '#2563eb' },
            { id: 'arealplan', label: 'Reguleringsplan', color: '#16a34a' },
            { id: 'flom', label: 'Flomsoner', color: '#0ea5e9' },
            { id: 'skred', label: 'Skredfareområder', color: '#dc2626' },
          ].map(layer => (
            <button
              key={layer.id}
              onClick={() => toggleLayer(layer.id)}
              className={cn(
                'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all font-medium',
                activeMapLayers.has(layer.id)
                  ? 'border-transparent text-white shadow-sm'
                  : 'border-gray-200 text-gray-600 bg-white hover:border-gray-300'
              )}
              style={activeMapLayers.has(layer.id) ? { backgroundColor: layer.color } : {}}
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: activeMapLayers.has(layer.id) ? 'white' : layer.color }}
              />
              {layer.label}
            </button>
          ))}
        </div>

        {/* Map */}
        {data.address && (
          <WizardMap
            lat={data.address.lat}
            lng={data.address.lng}
            zoom={17}
            className="h-64 border-t border-gray-100"
            showLayers
            activeLayers={activeMapLayers}
          />
        )}

        {/* Link to kommunens planregister */}
        {data.address?.municipalityNumber && (
          <div className="px-5 py-3 border-t border-gray-100">
            <a
              href={`https://arealplaner.no/${data.address.municipalityNumber}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              <ExternalLink className="w-4 h-4" />
              Se full reguleringsplan hos kommunen
            </a>
          </div>
        )}
      </div>

      {/* ── Section C: Faredata ─────────────────────────────────────────── */}
      {result.hazard && (result.hazard.flomFare !== 'ingen' || result.hazard.skredFare !== 'ingen') && (
        <div className="bg-white rounded-2xl border border-gray-200 p-5">
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
            Faredata (NVE)
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className={cn(
              'rounded-xl p-3 text-center',
              result.hazard.flomFare === 'høy' ? 'bg-red-50' :
              result.hazard.flomFare === 'middels' ? 'bg-amber-50' :
              result.hazard.flomFare === 'lav' ? 'bg-yellow-50' : 'bg-green-50'
            )}>
              <div className="text-2xl mb-1">🌊</div>
              <div className="text-xs text-gray-500 mb-0.5">Flomfare</div>
              <div className={cn(
                'text-sm font-bold capitalize',
                result.hazard.flomFare === 'høy' ? 'text-red-700' :
                result.hazard.flomFare === 'middels' ? 'text-amber-700' :
                result.hazard.flomFare === 'lav' ? 'text-yellow-700' : 'text-green-700'
              )}>
                {result.hazard.flomFare}
              </div>
            </div>
            <div className={cn(
              'rounded-xl p-3 text-center',
              result.hazard.skredFare === 'høy' ? 'bg-red-50' :
              result.hazard.skredFare === 'middels' ? 'bg-amber-50' :
              result.hazard.skredFare === 'lav' ? 'bg-yellow-50' : 'bg-green-50'
            )}>
              <div className="text-2xl mb-1">⛰️</div>
              <div className="text-xs text-gray-500 mb-0.5">Skredfare</div>
              <div className={cn(
                'text-sm font-bold capitalize',
                result.hazard.skredFare === 'høy' ? 'text-red-700' :
                result.hazard.skredFare === 'middels' ? 'text-amber-700' :
                result.hazard.skredFare === 'lav' ? 'text-yellow-700' : 'text-green-700'
              )}>
                {result.hazard.skredFare}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Section D: Dispensasjoner i nærheten ────────────────────────── */}
      <NearbyDispensations
        lat={data.address?.lat ?? 0}
        lng={data.address?.lng ?? 0}
        municipalityNumber={data.address?.municipalityNumber ?? ''}
        measureType={data.measureType ?? 'annet'}
      />

      {/* Next button */}
      <button
        onClick={onNext}
        className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 rounded-2xl transition-all text-base shadow-sm"
      >
        Neste: Se hva du kan gjøre
        <ChevronRight className="w-5 h-5" />
      </button>
    </div>
  )
}

// ── Nearby Dispensations component ───────────────────────────────────────────

interface NearbyDispensationsProps {
  lat: number
  lng: number
  municipalityNumber: string
  measureType: string
}

interface Dispensasjon {
  id: string
  title: string
  address: string
  date: string
  outcome: 'innvilget' | 'avslatt' | 'ukjent'
  description: string
  url?: string
  distance?: number
}

function NearbyDispensations({ lat, lng, municipalityNumber, measureType }: NearbyDispensationsProps) {
  const [dispensasjoner, setDispensasjoner] = useState<Dispensasjon[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!municipalityNumber) return
    fetchDispensasjoner()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [municipalityNumber])

  async function fetchDispensasjoner() {
    setLoading(true)
    setError(false)
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const res = await fetch(
        `${API_BASE}/dispensasjoner/nearby?lat=${lat}&lng=${lng}&municipality_number=${municipalityNumber}&measure_type=${measureType}&radius=1000`
      )
      if (!res.ok) throw new Error('Failed')
      const json = await res.json()
      setDispensasjoner(json.data ?? [])
    } catch {
      setError(true)
      setDispensasjoner([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-5">
      <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">
        Dispensasjoner i nærheten
      </div>
      <div className="text-base font-bold text-gray-900 mb-3">
        Har andre fått dispensasjon her?
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-2">
          <Loader2 className="w-4 h-4 animate-spin" />
          Søker i kommunens saksarkiv...
        </div>
      )}

      {!loading && error && (
        <div className="text-sm text-gray-500 py-2">
          Kunne ikke hente dispensasjonsdata fra kommunen akkurat nå.
        </div>
      )}

      {!loading && !error && dispensasjoner.length === 0 && (
        <div className="text-sm text-gray-500 py-2">
          Fant ingen registrerte dispensasjoner innenfor 1 km for denne tiltakstypen.
        </div>
      )}

      {!loading && dispensasjoner.length > 0 && (
        <div className="space-y-3">
          <div className="text-sm text-gray-600 mb-2">
            Fant <strong>{dispensasjoner.length} dispensasjon{dispensasjoner.length !== 1 ? 'er' : ''}</strong> innenfor 1 km:
          </div>
          {dispensasjoner.slice(0, 5).map(d => (
            <div key={d.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
              <div className={cn(
                'w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold mt-0.5',
                d.outcome === 'innvilget' ? 'bg-green-100 text-green-700' :
                d.outcome === 'avslatt' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-500'
              )}>
                {d.outcome === 'innvilget' ? '✓' : d.outcome === 'avslatt' ? '✗' : '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 truncate">{d.title}</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {d.address} · {d.date}
                  {d.distance && ` · ${d.distance} m unna`}
                </div>
                {d.description && (
                  <div className="text-xs text-gray-600 mt-1 line-clamp-2">{d.description}</div>
                )}
              </div>
              {d.url && (
                <a href={d.url} target="_blank" rel="noopener noreferrer" className="flex-shrink-0">
                  <ExternalLink className="w-4 h-4 text-gray-400 hover:text-blue-600" />
                </a>
              )}
            </div>
          ))}
          {dispensasjoner.length > 5 && (
            <div className="text-xs text-gray-500 text-center pt-1">
              + {dispensasjoner.length - 5} flere saker
            </div>
          )}
        </div>
      )}
    </div>
  )
}
