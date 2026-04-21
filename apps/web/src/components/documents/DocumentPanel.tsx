'use client'

import { useState } from 'react'
import { FileText, Download, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DocumentPanelProps {
  projectId: string
  applicationRequired?: boolean | null
  className?: string
}

type DocType = 'tiltaksbeskrivelse' | 'nabovarsel' | 'soknadsutkast' | 'pdf'

interface DocState {
  loading: boolean
  content: string | null
  error: string | null
}

const DOC_DEFS = [
  {
    id: 'tiltaksbeskrivelse' as DocType,
    title: 'Tiltaksbeskrivelse',
    description: 'Formell beskrivelse av det planlagte tiltaket for søknaden.',
    icon: '📝',
    legalBasis: 'SAK10 § 5-4',
    endpoint: '/documents/tiltaksbeskrivelse',
  },
  {
    id: 'nabovarsel' as DocType,
    title: 'Nabovarsel',
    description: 'Varselbrev til naboer og gjenboere i henhold til PBL § 21-3.',
    icon: '📬',
    legalBasis: 'PBL § 21-3',
    endpoint: '/documents/nabovarsel',
  },
  {
    id: 'soknadsutkast' as DocType,
    title: 'Søknadsveiledning',
    description: 'Strukturert veiledning for hva søknaden skal inneholde.',
    icon: '🗂️',
    legalBasis: 'PBL § 20-1',
    endpoint: '/documents/soknadsutkast',
  },
  {
    id: 'pdf' as DocType,
    title: 'Forhåndsvurderingsrapport (PDF)',
    description: 'Komplett rapport med alle funn, regelresultater og dokumentkrav.',
    icon: '📄',
    legalBasis: null,
    endpoint: '/documents/generate',
  },
]

export function DocumentPanel({ projectId, applicationRequired, className }: DocumentPanelProps) {
  const [docStates, setDocStates] = useState<Record<DocType, DocState>>({
    tiltaksbeskrivelse: { loading: false, content: null, error: null },
    nabovarsel: { loading: false, content: null, error: null },
    soknadsutkast: { loading: false, content: null, error: null },
    pdf: { loading: false, content: null, error: null },
  })
  const [activeDoc, setActiveDoc] = useState<DocType | null>(null)
  const [ownerName, setOwnerName] = useState('')
  const [ownerAddress, setOwnerAddress] = useState('')

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const generateDoc = async (docType: DocType) => {
    setDocStates(prev => ({
      ...prev,
      [docType]: { loading: true, content: null, error: null },
    }))
    setActiveDoc(docType)

    try {
      const def = DOC_DEFS.find(d => d.id === docType)!
      const body: Record<string, string> = { projectId }
      if (docType === 'nabovarsel') {
        body.ownerName = ownerName || '[Eiers navn]'
        body.ownerAddress = ownerAddress || '[Eiers adresse]'
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
        [docType]: { loading: false, content, error: null },
      }))
    } catch (err: any) {
      setDocStates(prev => ({
        ...prev,
        [docType]: { loading: false, content: null, error: 'Generering feilet. Prøv igjen.' },
      }))
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
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

      {/* Owner info for nabovarsel */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Dine opplysninger (for nabovarsel)
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
        </div>
      </div>

      {/* Document cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {DOC_DEFS.map(doc => {
          const state = docStates[doc.id]
          return (
            <div
              key={doc.id}
              className={cn(
                'border rounded-xl p-4 transition-all',
                activeDoc === doc.id && state.content
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-blue-200'
              )}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{doc.icon}</span>
                  <div>
                    <h4 className="text-sm font-bold text-gray-900">{doc.title}</h4>
                    {doc.legalBasis && (
                      <span className="text-xs text-gray-400 font-mono">{doc.legalBasis}</span>
                    )}
                  </div>
                </div>
                {state.content && (
                  <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                )}
              </div>
              <p className="text-xs text-gray-500 mb-3">{doc.description}</p>

              {state.error && (
                <div className="flex items-center gap-1 text-xs text-red-600 mb-2">
                  <AlertCircle className="w-3 h-3" />
                  {state.error}
                </div>
              )}

              <button
                onClick={() => generateDoc(doc.id)}
                disabled={state.loading}
                className={cn(
                  'w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium transition-colors',
                  state.loading
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : state.content
                    ? 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-200'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                )}
              >
                {state.loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Genererer...
                  </>
                ) : state.content ? (
                  <>
                    <Download className="w-4 h-4" />
                    Regenerer
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    Generer
                  </>
                )}
              </button>
            </div>
          )
        })}
      </div>

      {/* Document preview */}
      {activeDoc && docStates[activeDoc].content && (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <h4 className="text-sm font-bold text-gray-700">
              {DOC_DEFS.find(d => d.id === activeDoc)?.title}
            </h4>
            <button
              onClick={() => copyToClipboard(docStates[activeDoc].content!)}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Kopier tekst
            </button>
          </div>
          <div className="p-4 max-h-80 overflow-y-auto">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
              {docStates[activeDoc].content}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
