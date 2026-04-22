'use client'

import { useEffect } from 'react'
import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { getAnalysisResult } from '@/lib/api'
import { useProjectStore } from '@/store/projectStore'
import { MapView } from '@/components/map/MapView'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { RuleCard } from '@/components/ui/RuleCard'
import { DocumentPanel } from '@/components/documents/DocumentPanel'
import { getMeasureTypeLabel, formatDate } from '@/lib/utils'
import {
  CheckCircle,
  XCircle,
  HelpCircle,
  AlertTriangle,
  FileText,
  ArrowRight,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import Link from 'next/link'

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>()
  const { analysisResult, setAnalysisResult } = useProjectStore()

  const { data, isLoading, error } = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => getAnalysisResult(id),
    enabled: !!id && !analysisResult,
    staleTime: 5 * 60_000,
  })

  useEffect(() => {
    if (data) setAnalysisResult(data)
  }, [data, setAnalysisResult])

  const result = analysisResult ?? data

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Laster analyseresultat...</p>
        </div>
      </div>
    )
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Kunne ikke hente resultat</h2>
          <p className="text-gray-600 mb-6">
            Analysen ble ikke funnet. Sjekk at backend kjører og prøv igjen.
          </p>
          <Link
            href="/analyze"
            className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors"
          >
            Start ny analyse
          </Link>
        </div>
      </div>
    )
  }

  const blockingRules = result.ruleResults.filter((r) => r.blocking && r.status === 'fail')
  const warnRules = result.ruleResults.filter((r) => r.status === 'warn')
  const passRules = result.ruleResults.filter((r) => r.status === 'pass')
  const needsDispensation = result.ruleResults.some(
    (r) => r.ruleCode?.startsWith('DISP') || r.ruleGroup === 'dispensasjon'
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-7 h-7 bg-blue-600 rounded-md flex items-center justify-center">
                <span className="text-white text-xs font-bold">AB</span>
              </div>
              <span className="font-semibold text-gray-900 text-sm">AI Byggesøknad</span>
            </Link>
            <span className="text-gray-300">/</span>
            <span className="text-sm text-gray-600 truncate max-w-[200px]">
              {result.property
                ? `Gnr ${result.property.gnr} Bnr ${result.property.bnr}, ${result.property.municipality}`
                : `Prosjekt ${id}`}
            </span>
          </div>
          <Link
            href="/analyze"
            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            Ny analyse
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Status bar */}
      <div className="bg-white border-b border-gray-100 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-6">
          {/* Application required */}
          <div className="flex items-center gap-2">
            {result.applicationRequired === true ? (
              <AlertTriangle className="w-5 h-5 text-amber-500" />
            ) : result.applicationRequired === false ? (
              <CheckCircle className="w-5 h-5 text-green-500" />
            ) : (
              <HelpCircle className="w-5 h-5 text-gray-400" />
            )}
            <div>
              <div className="text-xs text-gray-500">Søknadsplikt</div>
              <div className="font-semibold text-sm text-gray-900">
                {result.applicationRequired === true
                  ? 'Søknadspliktig'
                  : result.applicationRequired === false
                  ? 'Trolig ikke søknadspliktig'
                  : 'Usikker – krever vurdering'}
              </div>
            </div>
          </div>

          <div className="h-8 w-px bg-gray-200" />

          {/* Risk level */}
          <div>
            <div className="text-xs text-gray-500 mb-1">Risikonivå</div>
            <RiskBadge level={result.riskLevel} />
          </div>

          <div className="h-8 w-px bg-gray-200" />

          {/* Measure type */}
          {result.classification && (
            <div>
              <div className="text-xs text-gray-500">Tiltakstype</div>
              <div className="font-semibold text-sm text-gray-900">
                {getMeasureTypeLabel(result.classification.measureType)}
                <span className="text-xs text-gray-400 ml-1">
                  ({Math.round(result.classification.confidence * 100)}% sikker)
                </span>
              </div>
            </div>
          )}

          <div className="h-8 w-px bg-gray-200" />

          {/* Rule summary */}
          <div className="flex items-center gap-3 text-sm">
            <span className="text-green-600 font-medium">{passRules.length} ok</span>
            <span className="text-amber-600 font-medium">{warnRules.length} advarsel</span>
            <span className="text-red-600 font-medium">{blockingRules.length} blokkerende</span>
          </div>

          <div className="ml-auto text-xs text-gray-400">
            Analysert {formatDate(result.analyzedAt)}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-[1fr_380px] gap-8">
          {/* Left – main content */}
          <div className="space-y-6">
            {/* AI Summary */}
            {result.aiSummary && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full" />
                  AI-oppsummering
                </h2>
                <p className="text-gray-700 leading-relaxed">{result.aiSummary}</p>
                <p className="text-xs text-gray-400 mt-3">
                  Basert på strukturerte data og regelmotor. Ikke juridisk rådgivning.
                </p>
              </div>
            )}

            {/* Map */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                <h2 className="font-semibold text-gray-900 text-sm">Kart og planlag</h2>
                {result.planLayer && (
                  <span className="text-xs text-gray-500">
                    {result.planLayer.planName ?? result.planLayer.planStatus}
                  </span>
                )}
              </div>
              <MapView className="h-80 rounded-none border-0" />
            </div>

            {/* Plan info */}
            {result.planLayer && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="font-semibold text-gray-900 mb-4">Planstatus</h2>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-500 text-xs mb-0.5">Planstatus</div>
                    <div className="font-medium text-gray-900 capitalize">
                      {result.planLayer.planStatus}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 text-xs mb-0.5">Arealformål</div>
                    <div className="font-medium text-gray-900 capitalize">
                      {result.planLayer.arealFormål}
                    </div>
                  </div>
                  {result.planLayer.utnyttelsesgrad && (
                    <div>
                      <div className="text-gray-500 text-xs mb-0.5">Utnyttelsesgrad</div>
                      <div className="font-medium text-gray-900">
                        {result.planLayer.utnyttelsesgrad}
                      </div>
                    </div>
                  )}
                  {result.planLayer.byggegrense && (
                    <div>
                      <div className="text-gray-500 text-xs mb-0.5">Byggegrense</div>
                      <div className="font-medium text-gray-900">
                        {result.planLayer.byggegrense} m
                      </div>
                    </div>
                  )}
                  {result.planLayer.hensynssoner.length > 0 && (
                    <div className="col-span-2">
                      <div className="text-gray-500 text-xs mb-0.5">Hensynssoner</div>
                      <div className="flex flex-wrap gap-1">
                        {result.planLayer.hensynssoner.map((h) => (
                          <span
                            key={h}
                            className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full"
                          >
                            {h}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Hazard info */}
            {result.hazard && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="font-semibold text-gray-900 mb-4">Faredata</h2>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-500 text-xs mb-0.5">Flomfare</div>
                    <div
                      className={`font-medium capitalize ${
                        result.hazard.flomFare === 'høy'
                          ? 'text-red-600'
                          : result.hazard.flomFare === 'middels'
                          ? 'text-amber-600'
                          : result.hazard.flomFare === 'lav'
                          ? 'text-green-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {result.hazard.flomFare}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 text-xs mb-0.5">Skredfare</div>
                    <div
                      className={`font-medium capitalize ${
                        result.hazard.skredFare === 'høy'
                          ? 'text-red-600'
                          : result.hazard.skredFare === 'middels'
                          ? 'text-amber-600'
                          : result.hazard.skredFare === 'lav'
                          ? 'text-green-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {result.hazard.skredFare}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Rule results */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Regelresultater</h2>
              <div className="space-y-2">
                {blockingRules.map((r) => (
                  <RuleCard key={r.ruleCode} rule={r} />
                ))}
                {warnRules.map((r) => (
                  <RuleCard key={r.ruleCode} rule={r} />
                ))}
                {passRules.map((r) => (
                  <RuleCard key={r.ruleCode} rule={r} />
                ))}
                {result.ruleResults.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    Ingen regelresultater tilgjengelig
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Right – sidebar */}
          <div className="space-y-4">
            {/* Next steps */}
            {result.nextSteps.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <ArrowRight className="w-4 h-4 text-blue-500" />
                  Neste steg
                </h3>
                <ol className="space-y-2">
                  {result.nextSteps.map((step, i) => (
                    <li key={i} className="flex gap-3 text-sm">
                      <span className="flex-shrink-0 w-5 h-5 bg-blue-100 text-blue-700 rounded-full text-xs flex items-center justify-center font-bold mt-0.5">
                        {i + 1}
                      </span>
                      <span className="text-gray-700 leading-relaxed">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Document requirements */}
            {result.documentRequirements.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-500" />
                  Sannsynlige dokumentkrav
                </h3>
                <ul className="space-y-1.5">
                  {result.documentRequirements.map((doc, i) => (
                    <li key={i} className="flex gap-2 text-sm text-gray-700">
                      <span className="text-gray-400 mt-0.5">·</span>
                      {doc}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Warnings */}
            {result.warnings.length > 0 && (
              <div className="bg-amber-50 rounded-xl border border-amber-200 p-5">
                <h3 className="font-semibold text-amber-900 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Viktige merknader
                </h3>
                <ul className="space-y-1.5">
                  {result.warnings.map((w, i) => (
                    <li key={i} className="text-sm text-amber-800 leading-relaxed">
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Property info */}
            {result.property && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3">Eiendom</h3>
                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Kommune</span>
                    <span className="text-gray-900 font-medium">{result.property.municipality}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Gnr/Bnr</span>
                    <span className="text-gray-900 font-medium">
                      {result.property.gnr}/{result.property.bnr}
                    </span>
                  </div>
                  {result.property.areal && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Areal</span>
                      <span className="text-gray-900 font-medium">{result.property.areal} m²</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Document generation */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <DocumentPanel
                projectId={id}
                applicationRequired={result.applicationRequired}
                needsDispensation={needsDispensation}
              />
            </div>

            {/* Disclaimer */}
            <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 text-xs text-gray-500 leading-relaxed">
              Vurderingen er basert på offentlig tilgjengelige data og en regelmotor. Den er
              veiledende og erstatter ikke kommunal saksbehandling eller juridisk rådgivning.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
