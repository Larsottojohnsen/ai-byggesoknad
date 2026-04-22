"use client";

import { useEffect, useState, useRef } from "react";

interface ProgressEvent {
  step: string;
  message: string;
  pct: number;
  done: boolean;
}

interface AnalysisProgressProps {
  projectId: string;
  onComplete: () => void;
}

const STEP_ICONS: Record<string, string> = {
  start: "🚀",
  municipality: "🗺️",
  classify: "🤖",
  property: "🏠",
  plan: "📋",
  hazard: "⚠️",
  rules: "⚖️",
  summary: "✍️",
  complete: "✅",
  timeout: "⏱️",
};

const STEP_LABELS: Record<string, string> = {
  start: "Starter analyse",
  municipality: "Identifiserer kommune",
  classify: "AI klassifiserer tiltak",
  property: "Henter eiendomsdata",
  plan: "Henter reguleringsplan",
  hazard: "Sjekker faredata (NVE)",
  rules: "Evaluerer regelverk",
  summary: "AI genererer oppsummering",
  complete: "Analyse fullført",
};

export default function AnalysisProgress({
  projectId,
  onComplete,
}: AnalysisProgressProps) {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [currentPct, setCurrentPct] = useState(0);
  const [isDone, setIsDone] = useState(false);
  const [currentMessage, setCurrentMessage] = useState("Kobler til...");
  const eventSourceRef = useRef<EventSource | null>(null);
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    if (!projectId) return;

    const es = new EventSource(`${API_BASE}/project/${projectId}/progress`);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      try {
        const evt: ProgressEvent = JSON.parse(e.data);
        setEvents((prev) => {
          // Avoid duplicates
          const exists = prev.some(
            (p) => p.step === evt.step && p.pct === evt.pct
          );
          if (exists) return prev;
          return [...prev, evt];
        });
        setCurrentPct(evt.pct);
        setCurrentMessage(evt.message);

        if (evt.done) {
          setIsDone(true);
          es.close();
          // Give user a moment to see 100% before navigating
          setTimeout(onComplete, 1200);
        }
      } catch {
        // Ignore parse errors
      }
    };

    es.onerror = () => {
      es.close();
      // If SSE fails, just proceed after a delay
      setTimeout(onComplete, 3000);
    };

    return () => {
      es.close();
    };
  }, [projectId, API_BASE, onComplete]);

  const completedSteps = events.filter((e) => e.pct > 0);

  return (
    <div className="w-full max-w-lg mx-auto">
      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-slate-700">
            {currentMessage}
          </span>
          <span className="text-sm font-semibold text-blue-600">
            {currentPct}%
          </span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${currentPct}%` }}
          />
        </div>
      </div>

      {/* Step list */}
      <div className="space-y-2">
        {Object.entries(STEP_LABELS).map(([stepKey, label]) => {
          const evt = completedSteps.find((e) => e.step === stepKey);
          const isActive =
            !isDone &&
            completedSteps.length > 0 &&
            completedSteps[completedSteps.length - 1]?.step === stepKey;
          const isCompleted = !!evt && !isActive;

          return (
            <div
              key={stepKey}
              className={`flex items-center gap-3 p-2.5 rounded-lg transition-all duration-300 ${
                isActive
                  ? "bg-blue-50 border border-blue-200"
                  : isCompleted
                  ? "bg-green-50"
                  : "opacity-40"
              }`}
            >
              <span className="text-lg w-7 text-center">
                {isActive ? (
                  <span className="inline-block animate-spin">⚙️</span>
                ) : isCompleted ? (
                  "✅"
                ) : (
                  STEP_ICONS[stepKey] || "○"
                )}
              </span>
              <span
                className={`text-sm ${
                  isActive
                    ? "font-semibold text-blue-700"
                    : isCompleted
                    ? "text-green-700"
                    : "text-slate-400"
                }`}
              >
                {label}
              </span>
              {isActive && (
                <span className="ml-auto flex gap-1">
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" />
                </span>
              )}
            </div>
          );
        })}
      </div>

      {isDone && (
        <div className="mt-6 text-center">
          <div className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-4 py-2 rounded-full font-medium">
            <span>✅</span>
            <span>Analyse fullført – videresender...</span>
          </div>
        </div>
      )}
    </div>
  );
}
