import React from 'react'
import { LucideIcon } from 'lucide-react'

export const PageHeader: React.FC<{
  title: string
  subtitle: string
  actions?: React.ReactNode
}> = ({ title, subtitle, actions }) => (
  <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-slate-100">{title}</h1>
      <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
    </div>
    {actions && <div className="flex flex-wrap items-center gap-2.5">{actions}</div>}
  </div>
)

export const Panel: React.FC<{
  title?: string
  subtitle?: string
  rightSlot?: React.ReactNode
  className?: string
  children: React.ReactNode
}> = ({ title, subtitle, rightSlot, className = '', children }) => (
  <section className={`enterprise-panel rounded-xl p-5 ${className}`}>
    {(title || rightSlot) && (
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          {title && <h2 className="text-sm font-semibold tracking-wide text-slate-100">{title}</h2>}
          {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
        </div>
        {rightSlot && <div className="shrink-0">{rightSlot}</div>}
      </div>
    )}
    {children}
  </section>
)

type AccentVariant = 'cyan' | 'emerald' | 'amber' | 'rose'

const ACCENT_MAP: Record<AccentVariant, string> = {
  cyan: 'border-cyan-500/25 bg-cyan-500/10 text-cyan-300',
  emerald: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300',
  amber: 'border-amber-500/25 bg-amber-500/10 text-amber-300',
  rose: 'border-rose-500/25 bg-rose-500/10 text-rose-300',
}

export const KpiCard: React.FC<{
  label: string
  value: string | number
  subtext?: string
  icon: LucideIcon
  accent?: AccentVariant
}> = ({ label, value, subtext, icon: Icon, accent = 'cyan' }) => (
  <div className="enterprise-panel enterprise-panel-hover rounded-xl p-4 sm:p-5">
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="text-xs font-medium uppercase tracking-wider text-slate-400">{label}</div>
        <div className="mt-2 font-mono text-2xl font-semibold tracking-tight text-slate-100">{value}</div>
        {subtext && <div className="mt-1.5 text-xs text-slate-400">{subtext}</div>}
      </div>
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${ACCENT_MAP[accent]}`}>
        <Icon className="h-5 w-5" />
      </div>
    </div>
  </div>
)

export const RiskBadge: React.FC<{ level: string; score?: number }> = ({ level, score }) => {
  const norm = level.toLowerCase()
  const styles =
    norm === 'high'
      ? 'border-rose-500/35 bg-rose-500/15 text-rose-300'
      : norm === 'moderate'
      ? 'border-amber-500/35 bg-amber-500/15 text-amber-300'
      : 'border-emerald-500/35 bg-emerald-500/15 text-emerald-300'
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles}`}>
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          norm === 'high' ? 'bg-rose-400' : norm === 'moderate' ? 'bg-amber-400' : 'bg-emerald-400'
        }`}
      />
      <span className="capitalize">{norm} Risk</span>
      {score !== undefined && <span className="font-mono opacity-85">({score.toFixed(0)}%)</span>}
    </span>
  )
}

export const LoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 4 }) => (
  <div className="space-y-4 animate-pulse">
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="h-28 rounded-xl bg-navy-850/80 border border-slate-800/70" />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="h-44 rounded-xl bg-navy-850/80 border border-slate-800/70" />
    ))}
  </div>
)
