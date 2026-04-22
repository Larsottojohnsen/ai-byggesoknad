'use client'

import { useState } from 'react'
import { FileText, Download, Loader2, CheckCircle, AlertCircle, Copy, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DocumentPanelProps {
  projectId: string
  applicationRequired?: boolean | null
  needsDispensation?: boolean
  className?: string
}

type DocType = 'tiltaksbeskrivelse' | 'nabovarsel' | 'soknadsutkast' | 'dispensasjonssoknad' | 'sjekkliste' | 'pdf'

interface DocState {
  loading: boolean
  content: string | null
  error: string | null
  expanded: boolean
}

const DOC_DEFS: Array<{
  id: DocType
  title: string
  description: string
  icon: string
  legalBasis: string | null
  endpoint: string
  requiresDispensation?: boolean
  alwaysShow?: boolean
}> = [
  {
    id: 'sjekkliste',
    title: 'Sjekkliste',
    description: 'Steg-for-steg sjekkliste for hele søknadsprosessen.',
    icon: '✅',
    legalBasis: null,
    endpoint: '/documents/sjekkliste',
    alwaysShow: true,
  },
  {
    id: 'tiltaksbeskrivelse',
    title: 'Tiltaksbeskrivelse',
    description: 'Formell beskrivelse av det planlagte tiltaket for søknaden.',
    icon: '📝',
    legalBasis: 'SAK10 § 5-4',
    endpoint: '/documents/tiltaksbeskrivelse',
  },
  {
    id: 'nabovarsel',
    title: 'Nabovarsel',
    description: 'Varselbrev til naboer og gjenboere (minst 2 uker ventetid).',
    icon: '📬',
    legalBasis: 'PBL § 21-3',
    endpoint: '/documents/nabovarsel',
  },
  {
    id: 'soknadsutkast',
    title: 'Søknadsveiledning',
    description: 'Strukturert veiledning for hva søknaden skal inneholde og hvilken type søknad som kreves.',
    icon: '🗂️',
    legalBasis: 'PBL § 20-1',
    endpoint: '/documents/soknadsutkast',
  },
  {
    id: 'dispensasjonssoknad',
    title: 'Dispensasjonssøknad',
    description: 'Søknad om dispensasjon fra reguleringsplan etter PBL § 19-1 med begrunnelse.',
    icon: '⚖️',
    legalBasis: 'PBL § 19-1, § 19-2',
    endpoint: '/documents/dispensasjonssoknad',
    requiresDispensation: true,
  },
  {
    id: 'pdf',
    title: 'Forhåndsvurderingsrapport (PDF)',
    description: 'Komplett rapport med alle funn, regelresultater og dokumentkrav.',
    icon: '📄',
    legalBasis: null,
    endpoint: '/documents/generate',
    alwaysShow: true,
  },
]

const initialDocState = (): DocState => ({ loading: false, content: null, error: null, expanded: false })

export function DocumentPanel({ projectId, applicationRequired, needsDispensation, className }: DocumentPanelProps) {
  const [docStates, setDocStates] = useState<Record<DocType, DocState>>({
    tiltaksbeskrivelse: initialDocState(),
    nabovarsel: initialDocState(),
    soknadsutkast: initialDocState(),
    dispensasjonssoknad: initialDocState(),
    sjekkliste: initialDocState(),
    pdf: initialDocState(),
  })
  const [ownerName, setOwnerName] = useState('')
  const [ownerAddress, setOwnerAddress] = useState('')
  const [ownerPhone, setOwnerPhone] = useState('')
  const [ownerEmail, setOwnerEmail] = useState('')
  const [copied, setCopied] = useState<DocType | null>(null)

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const visibleDocs = DOC_DEFS.filter(doc => {
    if (doc.alwaysShow) return true
    if (doc.requiresDispensation && !needsDispensation) return false
    if (applicationRequired === false) return false
    return true
  })

  const generateDoc = async (docType: DocType) => {
    setDocStates(prev => ({
      ...prev,
      [docType]: { ...prev[docType], loading: true, error: null },
    }))

    try {
      const def = DOC_DEFS.find(d => d.id === docType)!
      const body: Record<string, string> = { projectId }

      if (['nabovarsel', 'dispensasjonssoknad'].includes(docType)) {
        body.ownerName = ownerName || '[Eiers navn]'
        body.ownerAddress = ownerAddress || '[Eiers adresse]'
        body.ownerPhone = ownerPhone || '[Telefon]'
        body.ownerEmail = ownerEmail || '[E-post]'
      }
      if (docType === 'pdf') {
        body.type = 'forhåndsvurdering'
      }

      const res = await fetch(`${apiBase}${def.endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      const content = data.data?.content || data.data?.url || 'Dokument generert.'
      setDocStates(prev => ({
        ...prev,
        [docType]: { loading: false, content, error: null, expanded: true },
      }))
    } catch (err: any) {
      setDocStates(prev => ({
        ...prev,
        [docType]: { ...prev[docType], loading: false, error: 'Generering feilet. Prøv igjen.' },
      }))
    }
  }

  const copyToClipboard = async (docType: DocType, text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(docType)
    setTimeout(() => setCopied(null), 2000)
  }

  const toggleExpanded = (docType: DocType) => {
    setDocStates(prev => ({
      ...prev,
      [docType]: { ...prev[docType], expanded: !prev[docType].expanded },
    }))
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-bold text-gray-900">Dokumenter</h3>
        {applicationRequired && (
          <span className="ml-auto text-xs bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full font-medium">
            Søknadspliktig – dokumenter kreves
          </span>
        )}
      </div>

      {/* Owner info */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Dine opplysninger (for nabovarsel og dispensasjonssøknad)
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input
            type="text"
            placeholder="Ditt navn"
            value={ownerName}
            onChange={e => setOwnerName(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            placeholder="Din adresse"
            value={ownerAddress}
            onChange={e => setOwnerAddress(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="tel"
            placeholder="Telefon dagtid"
            value={ownerPhone}
            onChange={e => setOwnerPhone(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="email"
            placeholder="E-postadresse"
            value={ownerEmail}
            onChange={e => setOwnerEmail(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Document cards */}
      <div className="space-y-3">
        {visibleDocs.map(doc => {
          const state = docStates[doc.id]
          return (
            <div
              key={doc.id}
              className={cn(
                'border rounded-xl overflow-hidden transition-all',
                state.content
                  ? 'border-green-200 bg-green-50/30'
                  : 'border-gray-200 bg-white'
              )}
            >
              {/* Card header */}
              <div className="flex items-center gap-3 p-4">
                <span className="text-xl flex-shrink-0">{doc.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-gray-900">{doc.title}</h4>
                    {doc.legalBasis && (
                      <span className="text-xs text-gray-400 font-mono hidden sm:inline">{doc.legalBasis}</span>
                    )}
                    {state.content && (
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{doc.description}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {state.content && (
                    <button
                      onClick={() => toggleExpanded(doc.id)}
                      className="text-gray-400 hover:text-gray-600 p-1"
                    >
                      {state.expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  )}
                  <button
                    onClick={() => generateDoc(doc.id)}
                    disabled={state.loading}
                    className={cn(
                      'flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-medium transition-colors whitespace-nowrap',
                      state.loading
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : state.content
                        ? 'bg-white text-blue-600 hover:bg-blue-50 border border-blue-200'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    )}
                  >
                    {state.loading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Genererer...
                      </>
                    ) : state.content ? (
                      <>
                        <Download className="w-3.5 h-3.5" />
                        Regenerer
                      </>
                    ) : (
                      <>
                        <FileText className="w-3.5 h-3.5" />
                        Generer
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Error */}
              {state.error && (
                <div className="flex items-center gap-1.5 text-xs text-red-600 px-4 pb-3">
                  <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                  {state.error}
                </div>
              )}

              {/* Document content */}
              {state.content && state.expanded && (
                <div className="border-t border-gray-200">
                  <div className="bg-gray-50 px-4 py-2 flex items-center justify-between">
                    <span className="text-xs text-gray-500 font-medium">Forhåndsvisning</span>
                    <button
                      onClick={() => copyToClipboard(doc.id, state.content!)}
                      className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      <Copy className="w-3 h-3" />
                      {copied === doc.id ? 'Kopiert!' : 'Kopier tekst'}
                    </button>
                  </div>
                  <div className="p-4 max-h-96 overflow-y-auto bg-white">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                      {state.content}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Useful links */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
        <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2">Nyttige lenker</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
          {[
            { label: 'Søknadsskjemaer (DiBK)', url: 'https://www.dibk.no/soknad-og-skjema' },
            { label: 'Nabovarsel-veiledning (DiBK)', url: 'https://www.dibk.no/nabovarsel' },
            { label: 'Reguleringsplaner (arealplaner.no)', url: 'https://arealplaner.no' },
            { label: 'Grunnbokutskrift (seeiendom.no)', url: 'https://seeiendom.no' },
            { label: 'TEK17 (DiBK)', url: 'https://www.dibk.no/regelverk/byggteknisk-forskrift-tek17' },
            { label: 'SAK10 (DiBK)', url: 'https://www.dibk.no/regelverk/sak' },
          ].map(link => (
            <a
              key={link.url}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
            >
              → {link.label}
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
