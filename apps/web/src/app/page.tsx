import Link from 'next/link'
import { ArrowRight, CheckCircle, MapPin, FileText, Search, HelpCircle } from 'lucide-react'

const QUICK_STARTS = [
  { label: 'Garasje', icon: '🚗', type: 'garasje' },
  { label: 'Tilbygg', icon: '🏗️', type: 'tilbygg' },
  { label: 'Terrasse', icon: '🌿', type: 'veranda' },
  { label: 'Bruksendring', icon: '🔄', type: 'bruksendring' },
  { label: 'Kjeller/loft', icon: '🏠', type: 'kjeller_innredning' },
  { label: 'Annet', icon: '📋', type: 'annet' },
]

const HOW_IT_WORKS = [
  {
    step: '1',
    title: 'Søk opp eiendommen',
    desc: 'Skriv inn adressen din. Vi finner eiendommen automatisk.',
    icon: Search,
  },
  {
    step: '2',
    title: 'Velg hva du vil bygge',
    desc: 'Garasje, tilbygg, terrasse eller noe annet — velg fra listen.',
    icon: HelpCircle,
  },
  {
    step: '3',
    title: 'Få svar med en gang',
    desc: 'Vi sjekker reguleringsplan, faredata og regler automatisk.',
    icon: CheckCircle,
  },
  {
    step: '4',
    title: 'Last ned dokumenter',
    desc: 'Ferdig søknadsutkast, dispensasjonssøknad eller sjekkliste.',
    icon: FileText,
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-100 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-bold">AB</span>
            </div>
            <span className="font-semibold text-gray-900">AI Byggesøknad</span>
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/wizard" className="text-gray-600 hover:text-gray-900 transition-colors">
              Start vurdering
            </Link>
            <Link
              href="/wizard"
              className="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors font-medium"
            >
              Kom i gang gratis
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="px-6 py-16 text-center bg-gradient-to-b from-blue-50/50 to-white">
        <div className="max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 text-xs px-3 py-1.5 rounded-full mb-6 font-medium">
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
            Gratis · Ingen registrering · Svar på sekunder
          </div>

          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-5 leading-tight">
            Trenger du å søke om<br />
            <span className="text-blue-600">byggetillatelse?</span>
          </h1>

          <p className="text-lg text-gray-600 mb-8 leading-relaxed">
            Mange vet ikke om de trenger å søke — eller hva reguleringsplanen sier.
            Vi gir deg svaret på sekunder, basert på faktiske offentlige data.
          </p>

          <Link
            href="/wizard"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-2xl text-lg font-semibold hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 hover:shadow-blue-300"
          >
            Start gratis vurdering
            <ArrowRight className="w-5 h-5" />
          </Link>

          <p className="text-xs text-gray-400 mt-4">
            Brukt av boligeiere i hele Norge · Basert på Kartverket, NVE og kommunale data
          </p>
        </div>
      </section>

      {/* Quick start tiles */}
      <section className="px-6 py-10">
        <div className="max-w-2xl mx-auto">
          <p className="text-center text-sm font-semibold text-gray-500 mb-5 uppercase tracking-wider">
            Hva vil du bygge?
          </p>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {QUICK_STARTS.map(qs => (
              <Link
                key={qs.type}
                href={`/wizard?type=${qs.type}`}
                className="flex flex-col items-center gap-2 p-3 bg-white border-2 border-gray-100 rounded-2xl hover:border-blue-300 hover:bg-blue-50/50 transition-all group"
              >
                <span className="text-2xl">{qs.icon}</span>
                <span className="text-xs font-medium text-gray-700 group-hover:text-blue-700 text-center leading-tight">
                  {qs.label}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="px-6 py-14 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">
            Slik fungerer det
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {HOW_IT_WORKS.map(step => (
              <div key={step.step} className="flex flex-col items-center text-center gap-3">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-2xl flex items-center justify-center font-bold text-lg shadow-sm">
                  {step.step}
                </div>
                <div>
                  <div className="font-semibold text-gray-900 text-sm mb-1">{step.title}</div>
                  <div className="text-xs text-gray-500 leading-relaxed">{step.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* What you get */}
      <section className="px-6 py-14">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-3">
            Hva du får svar på
          </h2>
          <p className="text-gray-500 text-center mb-10 text-sm">
            Ikke teknisk sjargong — konkrete svar på det du faktisk lurer på.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { q: 'Trenger jeg å søke kommunen?', a: 'Tydelig ja/nei basert på SAK10 og tiltakstype' },
              { q: 'Hva sier reguleringsplanen?', a: 'Interaktivt kart med arealformål og byggegrenser' },
              { q: 'Er det fare for flom eller skred?', a: 'NVE-data for din eiendom' },
              { q: 'Har andre fått dispensasjon her?', a: 'Saker fra kommunens arkiv innenfor 1 km' },
              { q: 'Hva gjør jeg nå?', a: 'Steg-for-steg guide tilpasset din situasjon' },
              { q: 'Kan jeg få hjelp med søknaden?', a: 'Ferdig utfylte dokumenter klar for innsending' },
            ].map(item => (
              <div key={item.q} className="flex items-start gap-3 p-4 bg-white border border-gray-100 rounded-2xl shadow-sm">
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-gray-900 text-sm">{item.q}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{item.a}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-14 bg-blue-600 text-center">
        <div className="max-w-xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-3">
            Klar til å finne ut om du kan bygge?
          </h2>
          <p className="text-blue-100 mb-7 text-sm">
            Gratis vurdering på under 60 sekunder. Ingen registrering.
          </p>
          <Link
            href="/wizard"
            className="inline-flex items-center gap-2 bg-white text-blue-600 px-8 py-4 rounded-2xl text-base font-bold hover:bg-blue-50 transition-all shadow-lg"
          >
            Start nå
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Disclaimer + Footer */}
      <footer className="px-6 py-6 border-t border-gray-100">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 text-xs text-gray-400">
          <span>© 2026 AI Byggesøknad</span>
          <span className="text-center">
            Veiledende verktøy — erstatter ikke kommunal saksbehandling. Sjekk alltid med din kommune.
          </span>
          <span>Data: Kartverket · NVE · eInnsyn</span>
        </div>
      </footer>
    </div>
  )
}
