import axios from 'axios'
import type {
  AddressSuggestion,
  AnalysisResult,
  Project,
} from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// --- Address ---
export async function searchAddress(query: string): Promise<AddressSuggestion[]> {
  if (query.length < 3) return []
  const { data } = await apiClient.get('/address/search', { params: { q: query } })
  return data.data ?? []
}

// --- Project ---
export async function createProject(payload: {
  addressText: string
  lat: number
  lng: number
  intentText: string
}): Promise<Project> {
  const { data } = await apiClient.post('/project/create', payload)
  return data.data
}

export async function analyzeProject(projectId: string): Promise<AnalysisResult> {
  const { data } = await apiClient.post(`/project/${projectId}/analyze`)
  return data.data
}

export async function getProject(projectId: string): Promise<Project> {
  const { data } = await apiClient.get(`/project/${projectId}`)
  return data.data
}

export async function getAnalysisResult(projectId: string): Promise<AnalysisResult> {
  const { data } = await apiClient.get(`/project/${projectId}/results`)
  return data.data
}

// --- Documents ---
export async function generateReport(projectId: string): Promise<{ url: string }> {
  const { data } = await apiClient.post('/documents/generate', {
    projectId,
    type: 'forhåndsvurdering',
  })
  return data.data
}
