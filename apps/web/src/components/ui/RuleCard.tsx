import { cn, getRuleStatusColor, getRuleStatusIcon } from '@/lib/utils'
import type { RuleResult } from '@/types'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface RuleCardProps {
  rule: RuleResult
  className?: string
}

export function RuleCard({ rule, className }: RuleCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className={cn(
        'border rounded-lg overflow-hidden',
        getRuleStatusColor(rule.status),
        className
      )}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 p-3 text-left hover:opacity-80 transition-opacity"
      >
        <span className="flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold mt-0.5">
          {getRuleStatusIcon(rule.status)}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{rule.ruleName}</span>
            {rule.blocking && (
              <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium">
                Blokkerende
              </span>
            )}
          </div>
          <div className="text-xs opacity-70 mt-0.5">{rule.ruleCode} · {rule.ruleGroup}</div>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 flex-shrink-0 mt-0.5" />
        ) : (
          <ChevronDown className="w-4 h-4 flex-shrink-0 mt-0.5" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-3 pt-0 border-t border-current border-opacity-20">
          <p className="text-sm mt-2 leading-relaxed">{rule.explanation}</p>
          {rule.evidenceRefs.length > 0 && (
            <div className="mt-2">
              <span className="text-xs font-medium opacity-70">Kilder: </span>
              <span className="text-xs opacity-70">{rule.evidenceRefs.join(', ')}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
