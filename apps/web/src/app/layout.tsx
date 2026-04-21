import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Byggesøknad – Fra idé til søknad',
  description:
    'Norsk AI-plattform for byggesøknader. Sjekk søknadsplikt, hent geodata og generer dokumenter automatisk.',
  keywords: ['byggesøknad', 'plan og bygningsloven', 'reguleringsplan', 'tilbygg', 'bruksendring'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="nb">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
