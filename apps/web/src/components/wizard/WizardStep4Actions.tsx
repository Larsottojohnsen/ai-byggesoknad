'use client'

import { useState } from 'react'
import { ChevronLeft, Download, ExternalLink, CheckCircle, FileText, AlertTriangle, ArrowRight, Loader2 } from 'lucide-react'
import type { WizardData } from '@/app/wizard/page'
import { cn } from '@/lib/utils'

interface Props {
  data: WizardData
  onBack: () => void
}

type ActionPath = 'no_permit' | 'permit' | 'dispensation' | null

export function WizardStep4Actions({ data, onBack }: Props) {
  const [selectedPath, setSelectedPath] = useState<ActionPath>(null)
  const [generating, setGenerating] = useState(false)
  const [generatedDoc, setGeneratedDoc] = useState<string | null>(null)
  const [docError, setDocError] = useState<string | null>(null)

  const result = data.analysisResult
  const permitRequired = result?.applicationRequired === true
  const permitNotRequired = result?.applicationRequired === false
  const needsDispensation = result?.ruleResults.some(r => r.blocking && r.status === 'fail')

  // Auto-select path based on analysis
  const recommendedPath: ActionPath = needsDispensation
    ? 'dispensation'
    : permitRequired
    ? 'permit'
    : permitNotRequired
    ? 'no_permit'
    : 'permit'

  const activePath = selectedPath ?? recommendedPath

  async function handleGenerateDocument(docType: string) {
    if (!data.projectId) return
    setGenerating(true)
    setDocError(null)
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const res = await fetch(`${API_BASE}/documents/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectId: data.projectId, type: docType }),
      })
      if (!res.ok) throw new Error('Failed')
      const json = await res.json()
      setGeneratedDoc(json.data?.content ?? json.data?.url ?? null)
    } catch {
      setDocError('Kunne ikke generere dokument. Prøv igjen.')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* Back */}
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors">
        <ChevronLeft className="w-4 h-4" />
        Tilbake til vurdering
      </button>

      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Hva gjør du nå?</h1>
        <p className="text-gray-500 mt-1">Velg veien videre basert på vurderingen.</p>
      </div>

      {/* Path selector */}
      <div className="grid gap-3">
        {/* No permit needed */}
        <button
          onClick={() => setSelectedPath('no_permit')}
          className={cn(
            'w-full flex items-center gap-4 p-4 rounded-2xl border-2 text-left transition-all',
            activePath === 'no_permit'
              ? 'border-green-500 bg-green-50'
              : 'border-gray-200 bg-white hover:border-green-300'
          )}
        >
          <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <CheckCircle className="w-5 h-5 text-green-600" />
          </div>
          <div className="flex-1">
            <div className="font-semibold text-gray-900">Jeg kan bygge uten søknad</div>
            <div className="text-xs text-gray-500 mt-0.5">Sjekkliste for hva du må passe på</div>
          </div>
          {(permitNotRequired && !needsDispensation) && (
            <span className="text-xs bg-green-600 text-white px-2 py-1 rounded-full font-medium flex-shrink-0">
              Anbefalt
            </span>
          )}
        </button>

        {/* Permit required */}
        <button
          onClick={() => setSelectedPath('permit')}
          className={cn(
            'w-full flex items-center gap-4 p-4 rounded-2xl border-2 text-left transition-all',
            activePath === 'permit'
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 bg-white hover:border-blue-300'
          )}
        >
          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex-1">
            <div className="font-semibold text-gray-900">Send inn byggesøknad</div>
            <div className="text-xs text-gray-500 mt-0.5">Ferdig utfylt søknadsutkast til Altinn</div>
          </div>
          {(permitRequired && !needsDispensation) && (
            <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded-full font-medium flex-shrink-0">
              Anbefalt
            </span>
          )}
        </button>

        {/* Dispensation */}
        <button
          onClick={() => setSelectedPath('dispensation')}
          className={cn(
            'w-full flex items-center gap-4 p-4 rounded-2xl border-2 text-left transition-all',
            activePath === 'dispensation'
              ? 'border-amber-500 bg-amber-50'
              : 'border-gray-200 bg-white hover:border-amber-300'
          )}
        >
          <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
          </div>
          <div className="flex-1">
            <div className="font-semibold text-gray-900">Søk om dispensasjon</div>
            <div className="text-xs text-gray-500 mt-0.5">Ferdig dispensasjonssøknad med begrunnelse</div>
          </div>
          {needsDispensation && (
            <span className="text-xs bg-amber-600 text-white px-2 py-1 rounded-full font-medium flex-shrink-0">
              Anbefalt
            </span>
          )}
        </button>
      </div>

      {/* ── Path content ─────────────────────────────────────────────────── */}

      {activePath === 'no_permit' && (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-5 space-y-4 animate-in fade-in duration-200">
          <div className="font-semibold text-green-900">Sjekkliste — bygg uten søknad</div>
          <div className="space-y-2">
            {[
              'Tiltaket er under 50 m² BRA',
              'Gesimshøyde under 4,0 m og mønehøyde under 5,0 m',
              'Minst 1,0 m fra nabogrense (ellers trenger du nabosamtykke)',
              'Ikke i strid med reguleringsplan eller kommuneplan',
              'Ikke i flomsone eller skredsone',
              'Ikke på fredet eiendom eller i hensynssone',
              'Informer kommunen om tiltaket (ikke søknad, men melding)',
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="w-5 h-5 border-2 border-green-400 rounded flex-shrink-0 mt-0.5" />
                <span className="text-sm text-green-900">{item}</span>
              </div>
            ))}
          </div>
          <button
            onClick={() => handleGenerateDocument('sjekkliste')}
            disabled={generating || !data.projectId}
            className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold py-3 rounded-xl transition-all text-sm"
          >
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Last ned sjekkliste (PDF)
          </button>
        </div>
      )}

      {activePath === 'permit' && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 space-y-4 animate-in fade-in duration-200">
          <div className="font-semibold text-blue-900">Steg for steg — byggesøknad</div>
          <div className="space-y-3">
            {[
              { step: '1', title: 'Forhåndskonferanse', desc: 'Frivillig møte med kommunen for å avklare krav. Anbefales for større tiltak.' },
              { step: '2', title: 'Nabovarsel', desc: 'Send nabovarsel til alle naboer. De har 2 ukers frist til å protestere.' },
              { step: '3', title: 'Send søknad til kommunen', desc: 'Via Altinn (ByggSøk). Kommunen har 12 ukers behandlingstid.' },
              { step: '4', title: 'Igangsettingstillatelse', desc: 'Vent på tillatelse før du starter. Kan kombineres med rammetillatelse.' },
              { step: '5', title: 'Ferdigattest', desc: 'Søk om ferdigattest når tiltaket er ferdig. Kreves for å ta i bruk.' },
            ].map(s => (
              <div key={s.step} className="flex items-start gap-3">
                <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                  {s.step}
                </div>
                <div>
                  <div className="text-sm font-semibold text-blue-900">{s.title}</div>
                  <div className="text-xs text-blue-700 mt-0.5">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleGenerateDocument('søknadsutkast')}
              disabled={generating || !data.projectId}
              className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold py-3 rounded-xl transition-all text-sm"
            >
              {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              Søknadsutkast
            </button>
            <a
              href="https://www.altinn.no/skjemaoversikt/direktoratet-for-byggkvalitet/soknad-om-tillatelse-til-tiltak/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 bg-white border border-blue-300 text-blue-700 font-semibold py-3 rounded-xl transition-all text-sm hover:bg-blue-50"
            >
              <ExternalLink className="w-4 h-4" />
              Åpne Altinn
            </a>
          </div>
        </div>
      )}

      {activePath === 'dispensation' && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 space-y-4 animate-in fade-in duration-200">
          <div className="font-semibold text-amber-900">Dispensasjonssøknad</div>
          <p className="text-sm text-amber-800">
            Du trenger dispensasjon fordi tiltaket er i strid med gjeldende plan eller bestemmelse.
            En dispensasjonssøknad sendes til kommunen og behandles etter PBL §19-1.
          </p>

          {/* Blocking rules as basis for dispensation */}
          {result?.ruleResults.filter(r => r.blocking && r.status === 'fail').map(r => (
            <div key={r.ruleCode} className="bg-white/70 rounded-xl p-3">
              <div className="text-xs font-semibold text-amber-700 mb-1">Det søkes dispensasjon fra:</div>
              <div className="text-sm font-medium text-gray-900">{r.ruleName}</div>
              <div className="text-xs text-gray-600 mt-1">{r.explanation}</div>
              <div className="text-xs text-gray-400 mt-1">Hjemmel: {r.evidenceRefs.join(', ')}</div>
            </div>
          ))}

          <div className="space-y-3">
            {[
              { step: '1', title: 'Generer dispensasjonssøknad', desc: 'AI lager en ferdig begrunnet søknad basert på regelverket og lokale presedenssaker.' },
              { step: '2', title: 'Send nabovarsel', desc: 'Naboer og berørte parter må varsles om dispensasjonssøknaden.' },
              { step: '3', title: 'Send til kommunen', desc: 'Via Altinn eller kommunens postmottak. Behandlingstid: 12 uker.' },
            ].map(s => (
              <div key={s.step} className="flex items-start gap-3">
                <div className="w-6 h-6 bg-amber-600 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                  {s.step}
                </div>
                <div>
                  <div className="text-sm font-semibold text-amber-900">{s.title}</div>
                  <div className="text-xs text-amber-700 mt-0.5">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => handleGenerateDocument('dispensasjonssøknad')}
            disabled={generating || !data.projectId}
            className="w-full flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold py-3 rounded-xl transition-all text-sm"
          >
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            Generer dispensasjonssøknad
          </button>
        </div>
      )}

      {/* Generated document display */}
      {generatedDoc && (
        <div className="bg-white border border-gray-200 rounded-2xl p-5 animate-in fade-in duration-200">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="font-semibold text-gray-900">Dokument generert</span>
          </div>
          <pre className="text-xs text-gray-700 whitespace-pre-wrap bg-gray-50 rounded-xl p-4 max-h-64 overflow-y-auto font-mono leading-relaxed">
            {generatedDoc}
          </pre>
          <button
            onClick={() => {
              const blob = new Blob([generatedDoc], { type: 'text/plain' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = 'byggesoknad-dokument.txt'
              a.click()
            }}
            className="mt-3 w-full flex items-center justify-center gap-2 bg-gray-900 hover:bg-gray-800 text-white font-semibold py-3 rounded-xl transition-all text-sm"
          >
            <Download className="w-4 h-4" />
            Last ned
          </button>
        </div>
      )}

      {docError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800">
          {docError}
        </div>
      )}

      {/* Start over */}
      <div className="text-center pt-2">
        <a href="/wizard" className="text-sm text-gray-400 hover:text-gray-600 underline">
          Start en ny vurdering
        </a>
      </div>
    </div>
  )
}
