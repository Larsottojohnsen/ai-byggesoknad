'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight, Loader2, Info, MapPin, FileText, Zap } from 'lucide-react'
import { AddressSearch } from '@/components/analysis/AddressSearch'
import { MapView } from '@/components/map/MapView'
import AnalysisProgress from '@/components/analysis/AnalysisProgress'
import { useProjectStore } from '@/store/projectStore'
import { createProject, analyzeProject } from '@/lib/api'
import type { MeasureType } from '@/types'
import Link from 'next/link'

const MEASURE_SUGGESTIONS: { type: MeasureType; label: string; icon: string }[] = [
  { type: 'bruksendring', label: 'Bruksendring', icon: '🔄' },
  { type: 'tilbygg', label: 'Tilbygg', icon: '🏗️' },
  { type: 'garasje', label: 'Garasje', icon: '🚗' },
  { type: 'kjeller_innredning', label: 'Kjeller/loft', icon: '🏠' },
  { type: 'fasadeendring', label: 'Fasadeendring', icon: '🎨' },
  { type: 'veranda', label: 'Veranda/terrasse', icon: '🌿' },
]

export default function AnalyzePage() {
  const router = useRouter()
  const {
    selectedAddress,
    setSelectedAddress,
    intentText,
    setIntentText,
    setCurrentProject,
    setAnalysisResult,
    isAnalyzing,
    setIsAnalyzing,
  } = useProjectStore()

  const [error, setError] = useState<string | null>(null)
  const [projectId, setProjectId] = useState<string | null>(null)
  const [showProgress, setShowProgress] = useState(false)

  const canAnalyze = selectedAddress && intentText.trim().length >= 10

  async function handleAnalyze() {
    if (!canAnalyze) return
    setError(null)
    setIsAnalyzing(true)

    try {
      // Create project first
      const project = await createProject({
        addressText: selectedAddress!.addressText,
        lat: selectedAddress!.lat,
        lng: selectedAddress!.lng,
        intentText: intentText.trim(),
      })
      setCurrentProject(project)
      setProjectId(project.id)

      // Show progress overlay before starting analysis
      setShowProgress(true)

      // Start analysis (non-blocking – SSE will track progress)
      analyzeProject(project.id).then((result) => {
        setAnalysisResult(result)
      }).catch((err) => {
        console.error('Analysis error:', err)
      })

    } catch (err) {
      console.error(err)
      setError('Noe gikk galt. Sjekk at backend kjører og prøv igjen.')
      setIsAnalyzing(false)
    }
  }

  const handleProgressComplete = useCallback(() => {
    if (projectId) {
      router.push(`/project/${projectId}`)
    }
  }, [projectId, router])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-600 rounded-md flex items-center justify-center">
              <span className="text-white text-xs font-bold">AB</span>
            </div>
            <span className="font-semibold text-gray-900 text-sm">AI Byggesøknad</span>
          </Link>
          <span className="text-gray-300">/</span>
          <span className="text-sm text-gray-600">Ny vurdering</span>
        </div>
      </header>

      {/* Analysis Progress Modal */}
      {showProgress && projectId && (
        <div className="fixed inset-0 z-50 bg-white/90 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-8 w-full max-w-lg">
            <div className="text-center mb-8">
              <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Zap className="w-7 h-7 text-blue-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-1">Analyserer eiendommen</h2>
              <p className="text-sm text-gray-500">
                Vi henter data fra Kartverket, Geonorge og NVE...
              </p>
            </div>
            <AnalysisProgress
              projectId={projectId}
              onComplete={handleProgressComplete}
            />
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-[440px_1fr] gap-8">
          {/* Left panel – input */}
          <div className="space-y-5">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">Start vurdering</h1>
              <p className="text-gray-500 text-sm">
                Fyll inn adresse og beskriv hva du vil gjøre. Vi henter all nødvendig data automatisk.
              </p>
            </div>

            {/* Step 1 – Address */}
            <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-7 h-7 bg-blue-600 text-white rounded-full text-xs flex items-center justify-center font-bold shrink-0">
                  1
                </div>
                <div>
                  <div className="font-semibold text-gray-900 text-sm">Velg adresse</div>
                  <div className="text-xs text-gray-400">Søk etter adresse i Norge</div>
                </div>
                <MapPin className="w-4 h-4 text-gray-300 ml-auto" />
              </div>
              <AddressSearch
                onSelect={setSelectedAddress}
                value={selectedAddress}
                placeholder="F.eks. Storgata 1, Oslo"
              />
              {selectedAddress && (
                <div className="mt-3 flex items-center gap-2 bg-green-50 rounded-lg px-3 py-2">
                  <span className="text-green-500 text-sm">✓</span>
                  <div className="text-xs text-green-700">
                    <span className="font-medium">{selectedAddress.municipality}</span>
                    <span className="text-green-500 ml-1">
                      · {selectedAddress.lat.toFixed(5)}, {selectedAddress.lng.toFixed(5)}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Step 2 – Measure description */}
            <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-7 h-7 bg-blue-600 text-white rounded-full text-xs flex items-center justify-center font-bold shrink-0">
                  2
                </div>
                <div>
                  <div className="font-semibold text-gray-900 text-sm">Beskriv tiltaket</div>
                  <div className="text-xs text-gray-400">Hva ønsker du å gjøre?</div>
                </div>
                <FileText className="w-4 h-4 text-gray-300 ml-auto" />
              </div>

              {/* Quick suggestions */}
              <div className="flex flex-wrap gap-2 mb-3">
                {MEASURE_SUGGESTIONS.map((s) => (
                  <button
                    key={s.type}
                    onClick={() => {
                      if (!intentText) {
                        setIntentText(`Jeg ønsker å gjennomføre ${s.label.toLowerCase()}`)
                      }
                    }}
                    className="text-xs bg-gray-50 hover:bg-blue-50 hover:text-blue-700 text-gray-600 px-3 py-1.5 rounded-full transition-colors border border-gray-200 hover:border-blue-200 flex items-center gap-1"
                  >
                    <span>{s.icon}</span>
                    <span>{s.label}</span>
                  </button>
                ))}
              </div>

              <textarea
                value={intentText}
                onChange={(e) => setIntentText(e.target.value)}
                placeholder="Beskriv hva du vil gjøre med egne ord. F.eks: Jeg ønsker å gjøre om garasjen til en utleieleilighet..."
                rows={4}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
              <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
                <Info className="w-3 h-3" />
                <span>Minimum 10 tegn · {intentText.length} tegn skrevet</span>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* CTA */}
            <button
              onClick={handleAnalyze}
              disabled={!canAnalyze || isAnalyzing}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-4 rounded-2xl font-semibold hover:bg-blue-700 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-200 text-base"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Starter analyse...</span>
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  <span>Kjør AI-analyse</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            {/* What we check */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-4 text-sm border border-blue-100">
              <div className="font-semibold text-blue-900 mb-2.5 flex items-center gap-1.5">
                <Zap className="w-4 h-4" />
                Vi sjekker automatisk:
              </div>
              <ul className="space-y-1.5 text-blue-800">
                {[
                  '🗺️ Kommune og kommunespesifikke regler',
                  '📋 Reguleringsplan og arealformål (Geonorge)',
                  '🏠 Eiendomsdata (Kartverket Matrikkel)',
                  '⚠️ Flom- og skredfaredata (NVE Atlas)',
                  '⚖️ Søknadsplikt (PBL § 20-1, § 20-2, § 20-5)',
                  '📄 Dokumentkrav (SAK10) og neste steg',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-xs">
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right panel – map */}
          <div className="lg:sticky lg:top-20 h-[500px] lg:h-[calc(100vh-100px)]">
            <div className="w-full h-full rounded-2xl overflow-hidden border border-gray-200 shadow-sm">
              <MapView className="w-full h-full" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
