'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { WizardStep1Address } from '@/components/wizard/WizardStep1Address'
import { WizardStep2Measure } from '@/components/wizard/WizardStep2Measure'
import { WizardStep3Results } from '@/components/wizard/WizardStep3Results'
import { WizardStep4Actions } from '@/components/wizard/WizardStep4Actions'
import type { AddressSuggestion, MeasureType, AnalysisResult } from '@/types'
import Link from 'next/link'

export type WizardData = {
  address: AddressSuggestion | null
  measureType: MeasureType | null
  measureLabel: string
  analysisResult: AnalysisResult | null
  projectId: string | null
}

const STEPS = [
  { id: 1, label: 'Adresse' },
  { id: 2, label: 'Tiltak' },
  { id: 3, label: 'Vurdering' },
  { id: 4, label: 'Handling' },
]

export default function WizardPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [wizardData, setWizardData] = useState<WizardData>({
    address: null,
    measureType: null,
    measureLabel: '',
    analysisResult: null,
    projectId: null,
  })

  const updateData = useCallback((updates: Partial<WizardData>) => {
    setWizardData(prev => ({ ...prev, ...updates }))
  }, [])

  const goNext = useCallback(() => {
    setCurrentStep(prev => Math.min(prev + 1, 4))
  }, [])

  const goBack = useCallback(() => {
    setCurrentStep(prev => Math.max(prev - 1, 1))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-xs font-bold">AB</span>
            </div>
            <span className="font-semibold text-gray-900 text-sm">AI Byggesøknad</span>
          </Link>
          <span className="text-xs text-gray-400">Gratis vurdering</span>
        </div>
      </header>

      {/* Progress bar */}
      <div className="bg-white border-b border-gray-100 px-4 py-3">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center gap-0">
            {STEPS.map((step, i) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center gap-1">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                      step.id < currentStep
                        ? 'bg-blue-600 text-white'
                        : step.id === currentStep
                        ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    {step.id < currentStep ? '✓' : step.id}
                  </div>
                  <span
                    className={`text-xs font-medium whitespace-nowrap ${
                      step.id === currentStep ? 'text-blue-600' : 'text-gray-400'
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-1 mb-4 transition-all ${
                      step.id < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Step content */}
      <div className="max-w-2xl mx-auto px-4 py-8">
        {currentStep === 1 && (
          <WizardStep1Address
            data={wizardData}
            onUpdate={updateData}
            onNext={goNext}
          />
        )}
        {currentStep === 2 && (
          <WizardStep2Measure
            data={wizardData}
            onUpdate={updateData}
            onNext={goNext}
            onBack={goBack}
          />
        )}
        {currentStep === 3 && (
          <WizardStep3Results
            data={wizardData}
            onUpdate={updateData}
            onNext={goNext}
            onBack={goBack}
          />
        )}
        {currentStep === 4 && (
          <WizardStep4Actions
            data={wizardData}
            onBack={goBack}
          />
        )}
      </div>
    </div>
  )
}
