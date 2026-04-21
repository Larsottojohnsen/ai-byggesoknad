// ============================================================
// Shared domain types for AI Byggesøknad
// ============================================================

// --- Address ---
export interface AddressSuggestion {
  id: string
  text: string
  addressText: string
  municipality: string
  municipalityNumber: string
  postalCode?: string
  postalPlace?: string
  lat: number
  lng: number
}

// --- Property ---
export interface Property {
  id: string
  municipalityNumber: string
  municipality: string
  gnr: number   // gårdsnummer
  bnr: number   // bruksnummer
  fnr?: number  // festenummer
  snr?: number  // seksjonsnummer
  areal?: number
  buildingStatus?: string
  geometry?: GeoJSONFeature
  address?: string
}

// --- GeoJSON ---
export interface GeoJSONFeature {
  type: 'Feature'
  geometry: {
    type: string
    coordinates: unknown
  }
  properties?: Record<string, unknown>
}

// --- Plan Layer ---
export type PlanStatus = 'regulert' | 'kommuneplan' | 'uregulert' | 'ukjent'
export type ArealFormål =
  | 'boligbebyggelse'
  | 'næringsbebyggelse'
  | 'LNF'
  | 'samferdselsanlegg'
  | 'friområde'
  | 'annet'
  | 'ukjent'

export interface PlanLayerResult {
  planId?: string
  planName?: string
  planStatus: PlanStatus
  arealFormål: ArealFormål
  hensynssoner: string[]
  byggegrense?: number  // meters
  utnyttelsesgrad?: string  // e.g. "BYA=30%"
  planUrl?: string
  geometry?: GeoJSONFeature
}

// --- Hazard ---
export type HazardLevel = 'ingen' | 'lav' | 'middels' | 'høy' | 'ukjent'

export interface HazardResult {
  flomFare: HazardLevel
  skredFare: HazardLevel
  flomSoneId?: string
  skredSoneId?: string
  notes?: string
}

// --- Measure / Tiltak ---
export type MeasureType =
  | 'bruksendring'
  | 'tilbygg'
  | 'påbygg'
  | 'garasje'
  | 'carport'
  | 'kjeller_innredning'
  | 'loft_innredning'
  | 'fasadeendring'
  | 'terrenginngrep'
  | 'støttemur'
  | 'veranda'
  | 'tomtedeling'
  | 'annet'
  | 'ukjent'

export interface MeasureClassification {
  measureType: MeasureType
  confidence: number  // 0-1
  requiresPermit: boolean | null  // null = usikker
  requiresResponsibility: boolean | null
  notes?: string
}

// --- Rule Engine ---
export type RuleStatus = 'pass' | 'warn' | 'fail' | 'unknown'

export interface RuleResult {
  ruleCode: string
  ruleName: string
  ruleGroup: string
  status: RuleStatus
  explanation: string
  evidenceRefs: string[]
  blocking: boolean
  sourceVersion: string
}

// --- Risk ---
export type RiskLevel = 'lav' | 'middels' | 'høy' | 'ukjent'

// --- Project ---
export type ProjectStatus =
  | 'draft'
  | 'analyzing'
  | 'analyzed'
  | 'preparing'
  | 'ready'
  | 'submitted'

export interface Project {
  id: string
  addressText: string
  lat: number
  lng: number
  intentText: string
  measureType?: MeasureType
  status: ProjectStatus
  riskLevel?: RiskLevel
  applicationRequired?: boolean | null
  createdAt: string
  updatedAt: string
}

// --- Analysis Result ---
export interface AnalysisResult {
  projectId: string
  property?: Property
  planLayer?: PlanLayerResult
  hazard?: HazardResult
  classification?: MeasureClassification
  ruleResults: RuleResult[]
  riskLevel: RiskLevel
  applicationRequired: boolean | null
  aiSummary?: string
  nextSteps: string[]
  documentRequirements: string[]
  warnings: string[]
  analyzedAt: string
}

// --- API Responses ---
export interface ApiResponse<T> {
  data: T
  success: boolean
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}
