import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { RiskLevel, RuleStatus } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'lav': return 'text-green-600 bg-green-50 border-green-200'
    case 'middels': return 'text-amber-600 bg-amber-50 border-amber-200'
    case 'høy': return 'text-red-600 bg-red-50 border-red-200'
    default: return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

export function getRiskLabel(level: RiskLevel): string {
  switch (level) {
    case 'lav': return 'Lav risiko'
    case 'middels': return 'Middels risiko'
    case 'høy': return 'Høy risiko'
    default: return 'Ukjent risiko'
  }
}

export function getRuleStatusColor(status: RuleStatus): string {
  switch (status) {
    case 'pass': return 'text-green-700 bg-green-50 border-green-200'
    case 'warn': return 'text-amber-700 bg-amber-50 border-amber-200'
    case 'fail': return 'text-red-700 bg-red-50 border-red-200'
    default: return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

export function getRuleStatusIcon(status: RuleStatus): string {
  switch (status) {
    case 'pass': return '✓'
    case 'warn': return '!'
    case 'fail': return '✗'
    default: return '?'
  }
}

export function getMeasureTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    bruksendring: 'Bruksendring',
    tilbygg: 'Tilbygg',
    påbygg: 'Påbygg',
    garasje: 'Garasje',
    carport: 'Carport',
    kjeller_innredning: 'Innredning av kjeller',
    loft_innredning: 'Innredning av loft',
    fasadeendring: 'Fasadeendring',
    terrenginngrep: 'Terrenginngrep',
    støttemur: 'Støttemur',
    veranda: 'Veranda/balkong',
    tomtedeling: 'Tomtedeling',
    annet: 'Annet tiltak',
    ukjent: 'Ukjent tiltak',
  }
  return labels[type] ?? type
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('nb-NO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
