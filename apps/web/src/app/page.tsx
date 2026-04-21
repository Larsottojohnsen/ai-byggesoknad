import Link from 'next/link'
import { ArrowRight, CheckCircle, MapPin, FileText, Zap } from 'lucide-react'

const USE_CASES = [
  { label: 'Bruksendring', desc: 'Gjøre om bod til boenhet?' },
  { label: 'Tilbygg', desc: 'Utvide boligen din?' },
  { label: 'Garasje', desc: 'Bygge ny garasje?' },
  { label: 'Kjeller/loft', desc: 'Innrede kjeller eller loft?' },
]

const FEATURES = [
  {
    icon: MapPin,
    title: 'Automatisk geodatainnhenting',
    desc: 'Vi henter reguleringsplan, arealformål og faredata fra Kartverket og NVE automatisk.',
  },
  {
    icon: Zap,
    title: 'AI-klassifisering av tiltak',
    desc: 'Beskriv hva du vil gjøre med egne ord – AI klassifiserer tiltaket og aktiverer riktige regler.',
  },
  {
    icon: CheckCircle,
    title: 'Regelmotor basert på PBL',
    desc: 'Strukturert vurdering av søknadsplikt, ansvarsrett og dokumentkrav – ikke bare en chatbot.',
  },
  {
    icon: FileText,
    title: 'PDF-rapport og dokumenter',
    desc: 'Generer forhåndsvurderingsrapport, tiltaksbeskrivelse og nabovarselutkast.',
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-100 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-bold">AB</span>
            </div>
            <span className="font-semibold text-gray-900">AI Byggesøknad</span>
          </div>
          <nav className="flex items-center gap-6 text-sm text-gray-600">
            <Link href="/analyze" className="hover:text-gray-900 transition-colors">
              Start vurdering
            </Link>
            <Link
              href="/analyze"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Kom i gang
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="px-6 py-20 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded-full mb-6">
            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
            Fase 1 – Forhåndsvurdering
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
            Fra byggeide til<br />
            <span className="text-blue-600">søknadsvurdering</span> på sekunder
          </h1>
          <p className="text-xl text-gray-600 mb-10 leading-relaxed">
            Skriv inn adressen din og beskriv hva du vil bygge. Vi henter reguleringsplan,
            faredata og vurderer søknadsplikt automatisk – basert på faktiske offentlige data.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/analyze"
              className="flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-xl text-lg font-medium hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200"
            >
              Start gratis vurdering
              <ArrowRight className="w-5 h-5" />
            </Link>
            <button className="text-gray-600 hover:text-gray-900 px-6 py-4 transition-colors">
              Se eksempelrapport
            </button>
          </div>
        </div>
      </section>

      {/* Use cases */}
      <section className="px-6 py-12 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <p className="text-center text-sm text-gray-500 mb-6 uppercase tracking-wide">
            Vanlige tiltak vi vurderer
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {USE_CASES.map((uc) => (
              <Link
                key={uc.label}
                href={`/analyze?type=${uc.label.toLowerCase()}`}
                className="bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-sm transition-all group"
              >
                <div className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                  {uc.label}
                </div>
                <div className="text-sm text-gray-500 mt-1">{uc.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-4">
            Ikke bare en chatbot
          </h2>
          <p className="text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            AI Byggesøknad kombinerer strukturerte offentlige geodata med en regelmotor
            basert på plan- og bygningsloven. AI forklarer og oppsummerer – fakta er alltid i sentrum.
          </p>
          <div className="grid md:grid-cols-2 gap-8">
            {FEATURES.map((f) => (
              <div key={f.title} className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <f.icon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">{f.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="px-6 py-8 bg-amber-50 border-t border-amber-100">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-sm text-amber-800">
            <strong>Viktig:</strong> AI Byggesøknad er et privat beslutningsstøtteverktøy og er ikke
            en offentlig myndighet. Vurderinger er veiledende og erstatter ikke kommunal saksbehandling.
            Sjekk alltid med din kommune ved tvil.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-gray-100">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-gray-500">
          <span>© 2026 AI Byggesøknad</span>
          <span>Bygget med data fra Kartverket, Geonorge og NVE</span>
        </div>
      </footer>
    </div>
  )
}
