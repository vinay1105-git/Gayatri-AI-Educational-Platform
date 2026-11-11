import React, { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'
import { LoadingSkeleton, PageHeader, Panel } from '../components/UiPrimitives'
import type { TrajectoryPoint } from '../types'

interface StudentAnalyticsPayload {
  trajectory: TrajectoryPoint[]
  study_cadence: Array<{
    week_label: string
    study_hours: number
    sessions_count: number
    assignments_completed: number
    avg_quiz_score: number
    attendance_pct: number
  }>
  concept_comparison: Array<{
    concept_code: string
    concept_name: string
    course_code: string
    student_mastery: number
    cohort_mean: number
    attempts: number
  }>
}

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<StudentAnalyticsPayload | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<StudentAnalyticsPayload>('/analytics/student')
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSkeleton />
  if (!data) return <div className="enterprise-panel rounded-xl p-6 text-slate-400">Analytics unavailable.</div>

  return (
    <div className="space-y-6">
      <PageHeader
        title="Longitudinal Learning Analytics"
        subtitle="Comparative concept mastery against cohort benchmarks and weekly engagement cadence"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel
          title="Weekly Study Hours vs Quiz Score Correlation"
          subtitle="Dual-axis view of effort volume against academic assessment averages"
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data.study_cadence} margin={{ top: 10, right: 10, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis dataKey="week_label" stroke="#64748B" fontSize={11} />
                <YAxis yAxisId="left" stroke="#64748B" fontSize={11} domain={[0, 28]} />
                <YAxis yAxisId="right" orientation="right" stroke="#64748B" fontSize={11} domain={[35, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar yAxisId="left" dataKey="study_hours" fill="#0EA5E9" radius={[4, 4, 0, 0]} name="Study Hours" />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="avg_quiz_score"
                  stroke="#10B981"
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                  name="Quiz Average (%)"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title="Concept Mastery vs Cohort Benchmark"
          subtitle="Comparing your lowest-scoring concepts directly against institutional averages"
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.concept_comparison.slice(0, 10)}
                margin={{ top: 10, right: 12, left: -12, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis
                  dataKey="concept_code"
                  stroke="#64748B"
                  fontSize={10}
                  angle={-25}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis domain={[0, 100]} stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar dataKey="student_mastery" fill="#22D3EE" radius={[4, 4, 0, 0]} name="Your Mastery (%)" />
                <Bar dataKey="cohort_mean" fill="#64748B" radius={[4, 4, 0, 0]} name="Cohort Mean (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <Panel title="Complete Concept Mastery Matrix" subtitle="Detailed breakdown of tracked concepts across enrolled courses">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 pr-3">Course</th>
                <th className="py-2.5 px-3">Concept</th>
                <th className="py-2.5 px-3">Your Mastery</th>
                <th className="py-2.5 px-3">Cohort Mean</th>
                <th className="py-2.5 px-3">Gap vs Cohort</th>
                <th className="py-2.5 pl-3 text-right">Interactions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {data.concept_comparison.map((c) => {
                const delta = c.student_mastery - c.cohort_mean
                return (
                  <tr key={c.concept_code} className="hover:bg-navy-800/40">
                    <td className="py-2.5 pr-3 font-mono text-cyan-300">{c.course_code}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-100">{c.concept_name}</td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-slate-100">{c.student_mastery}%</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">{c.cohort_mean}%</td>
                    <td className="py-2.5 px-3 font-mono">
                      <span className={delta >= 0 ? 'text-emerald-400' : 'text-amber-400'}>
                        {delta >= 0 ? `+${delta.toFixed(1)}%` : `${delta.toFixed(1)}%`}
                      </span>
                    </td>
                    <td className="py-2.5 pl-3 text-right font-mono text-slate-400">{c.attempts}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}
