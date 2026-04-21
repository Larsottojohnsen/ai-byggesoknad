'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight, Loader2, Info } from 'lucide-react'
import { AddressSearch } from '@/components/analysis/AddressSearch'
import { MapView } from '@/components/map/MapView'
import { useProjectStore } from '@/store/projectStore'
import { createProject, analyzeProject } from '@/lib/api'
import { getMeasureTypeLabel } from '@/lib/utils'
import type { MeasureType } from '@/types'
import Link from 'next/link'

const MEASURE_SUGGESTIONS: { type: MeasureType; label: string; desc: string }[] = [
  { type: 'bruksendring', label: 'Bruksendring', desc: 'Endre bruk av rom eller bygning' },
  { type: 'tilbygg', label: 'Tilbygg', desc: 'Utvide eksisterende bygning' },
  { type: 'garasje', label: 'Garasje', desc: 'Bygge ny garasje eller carport' },
  { type: 'kjeller_innredning', label: 'Kjeller/loft', desc: 'Innrede kjeller eller loft' },
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
  const [analysisStep, setAnalysisStep] = useState<string | null>(null)

  const canAnalyze = selectedAddress && intentText.trim().length >= 10

  async function handleAnalyze() {
    if (!canAnalyze) return
    setError(null)
    setIsAnalyzing(true)

    try {
      setAnalysisStep('Oppretter prosjekt...')
      const project = await createProject({
        addressText: selectedAddress!.addressText,
        lat: selectedAddress!.lat,
        lng: selectedAddress!.lng,
        intentText: intentText.trim(),
      })
      setCurrentProject(project)

      setAnalysisStep('Henter geodata og reguleringsplan...')
      await new Promise((r) => setTimeout(r, 800))

      setAnalysisStep('Kjører regelmotor...')
      const result = await analyzeProject(project.id)
      setAnalysisResult(result)

      router.push(`/project/${project.id}`)
    } catch (err) {
      console.error(err)
      setError('Noe gikk galt under analysen. Sjekk at backend kjører og prøv igjen.')
    } finally {
      setIsAnalyzing(false)
      setAnalysisStep(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-4">
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

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-[420px_1fr] gap-8">
          {/* Left panel – input */}
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">Start vurdering</h1>
              <p className="text-gray-600 text-sm">
                Fyll inn adresse og beskriv hva du vil gjøre. Vi henter all nødvendig data automatisk.
              </p>
            </div>

            {/* Step 1 – Address */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-6 h-6 bg-blue-600 text-white rounded-full text-xs flex items-center justify-center font-bold">
                  1
                </span>
                <span className="font-medium text-gray-900">Velg adresse</span>
              </div>
              <AddressSearch
                onSelect={setSelectedAddress}
                value={selectedAddress}
                placeholder="F.eks. Storgata 1, Oslo"
              />
              {selectedAddress && (
                <div className="mt-2 text-xs text-green-600 flex items-center gap-1">
                  <span>✓</span>
                  <span>
                    {selectedAddress.municipality} · {selectedAddress.lat.toFixed(5)}, {selectedAddress.lng.toFixed(5)}
                  </span>
                </div>
              )}
            </div>

            {/* Step 2 – Measure description */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-6 h-6 bg-blue-600 text-white rounded-full text-xs flex items-center justify-center font-bold">
                  2
                </span>
                <span className="font-medium text-gray-900">Beskriv tiltaket</span>
              </div>

              {/* Quick suggestions */}
              <div className="flex flex-wrap gap-2 mb-3">
                {MEASURE_SUGGESTIONS.map((s) => (
                  <button
                    key={s.type}
                    onClick={() =>
                      setIntentText(
                        intentText
                          ? intentText
                          : `Jeg ønsker å gjennomføre ${s.label.toLowerCase()}`
                      )
                    }
                    className="text-xs bg-gray-100 hover:bg-blue-50 hover:text-blue-700 text-gray-600 px-3 py-1.5 rounded-full transition-colors border border-transparent hover:border-blue-200"
                  >
                    {s.label}
                  </button>
                ))}
              </div>

              <textarea
                value={intentText}
                onChange={(e) => setIntentText(e.target.value)}
                placeholder="Beskriv hva du vil gjøre med egne ord. F.eks: Jeg ønsker å gjøre om garasjen til en utleieleilighet..."
                rows={4}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
              <div className="flex items-center gap-1 mt-1.5 text-xs text-gray-400">
                <Info className="w-3 h-3" />
                <span>Minimum 10 tegn. Jo mer detaljer, jo bedre vurdering.</span>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* CTA */}
            <button
              onClick={handleAnalyze}
              disabled={!canAnalyze || isAnalyzing}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-3.5 rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-200"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>{analysisStep ?? 'Analyserer...'}</span>
                </>
              ) : (
                <>
                  <span>Kjør analyse</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            {/* What we check */}
            <div className="bg-blue-50 rounded-xl p-4 text-sm">
              <div className="font-medium text-blue-900 mb-2">Vi sjekker automatisk:</div>
              <ul className="space-y-1 text-blue-800">
                {[
                  'Reguleringsplan og arealformål',
                  'Hensynssoner og byggegrenser',
                  'Flom- og skredfaredata (NVE)',
                  'Søknadsplikt (PBL § 20-1, § 20-2, § 20-5)',
                  'Dokumentkrav og neste steg',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2">
                    <span className="text-blue-500">·</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right panel – map */}
          <div className="lg:sticky lg:top-8 h-[500px] lg:h-[calc(100vh-120px)]">
            <MapView className="w-full h-full" />
          </div>
        </div>
      </div>
    </div>
  )
}
