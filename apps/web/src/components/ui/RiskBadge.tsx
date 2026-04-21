import { cn, getRiskColor, getRiskLabel } from '@/lib/utils'
import type { RiskLevel } from '@/types'

interface RiskBadgeProps {
  level: RiskLevel
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export function RiskBadge({ level, className, size = 'md' }: RiskBadgeProps) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-2',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium rounded-full border',
        getRiskColor(level),
        sizeClasses[size],
        className
      )}
    >
      <span
        className={cn('w-2 h-2 rounded-full', {
          'bg-green-500': level === 'lav',
          'bg-amber-500': level === 'middels',
          'bg-red-500': level === 'høy',
          'bg-gray-400': level === 'ukjent',
        })}
      />
      {getRiskLabel(level)}
    </span>
  )
}
