import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowUpRight,
  Download,
  GraduationCap,
  ShieldAlert,
  TrendingUp,
  Users,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts'
import { api } from '../api/client'
import { KpiCard, LoadingSkeleton, PageHeader, Panel, RiskBadge } from '../components/UiPrimitives'
import type { CohortAnalyticsPayload } from '../types'

const CLUSTER_COLORS: Record<string, string> = {
  'Accelerated Mastery': '#22D3EE',
  'Consistent Builder': '#10B981',
  'Developing Momentum': '#F59E0B',
  'Targeted Support Needed': '#F43F5E',
}

export const AdminDashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const [data, setData] = useState<CohortAnalyticsPayload | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<CohortAnalyticsPayload>('/analytics/cohort')
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSkeleton />
  if (!data) return <div className="enterprise-panel rounded-xl p-6 text-rose-300">Unable to load cohort telemetry.</div>

  const { kpis, cohort_comparison, weekly_trends, concept_analytics, cluster_scatter, score_distribution, priority_students } =
    data

  // Group scatter points by cluster label for legend rendering
  const clusterGroups = Object.keys(CLUSTER_COLORS).map((label) => ({
    label,
    color: CLUSTER_COLORS[label],
    points: cluster_scatter.filter((p) => p.cluster_label === label),
  }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Enterprise Academic Command Center"
        subtitle={`Real-time institutional intelligence across ${kpis.total_students} learners and ${kpis.total_submissions} graded evaluations`}
        actions={
          <>
            <button
              type="button"
              onClick={() => navigate('/admin/ml-models')}
              className="rounded-lg border border-cyan-500/35 bg-cyan-500/15 px-3.5 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/25"
            >
              ML Model Console
            </button>
            <button
              type="button"
              onClick={() => api.download('/reports/cohort/pdf', 'Gayatri_AI_Executive_Cohort_Report.pdf')}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-navy-850 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500"
            >
              <Download className="h-4 w-4 text-emerald-400" />
              Export Executive PDF
            </button>
          </>
        }
      />

      {/* Executive KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Active Learners"
          value={kpis.total_students}
          subtext={`Mean GPA ${kpis.avg_gpa.toFixed(2)} · Attendance ${kpis.avg_attendance_rate.toFixed(1)}%`}
          icon={Users}
          accent="cyan"
        />
        <KpiCard
          label="Mean Projected Score"
          value={`${kpis.avg_predicted_score.toFixed(1)}%`}
          subtext={`Engagement Index ${kpis.avg_engagement_index.toFixed(1)} / 100`}
          icon={TrendingUp}
          accent="emerald"
        />
        <KpiCard
          label="High-Risk Learners"
          value={kpis.high_risk_count}
          subtext={`${kpis.moderate_risk_count} moderate · ${kpis.low_risk_count} low risk`}
          icon={AlertTriangle}
          accent="rose"
        />
        <KpiCard
          label="Open Interventions"
          value={kpis.open_interventions}
          subtext="Active advisor outreach cases"
          icon={ShieldAlert}
          accent="amber"
        />
      </div>

      {/* Institutional Weekly Trend + K-Means PCA Scatter */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel
          title="10-Week Institutional Engagement & Quiz Trend"
          subtitle="Cohort-wide mean weekly quiz performance and study hours"
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weekly_trends} margin={{ top: 10, right: 16, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis dataKey="week_label" stroke="#64748B" fontSize={11} />
                <YAxis domain={[55, 95]} stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Line type="monotone" dataKey="avg_quiz_score" stroke="#22D3EE" strokeWidth={2.4} name="Mean Quiz (%)" />
                <Line type="monotone" dataKey="avg_attendance" stroke="#10B981" strokeWidth={2} name="Attendance (%)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title="K-Means Learner Persona Segmentation (PCA 2D)"
          subtitle="Unsupervised behavioral clustering across mastery, consistency, attendance, and slope"
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 16, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis type="number" dataKey="pca_x" name="PC1" stroke="#64748B" fontSize={11} />
                <YAxis type="number" dataKey="pca_y" name="PC2" stroke="#64748B" fontSize={11} />
                <ZAxis type="number" dataKey="predicted_score" range={[35, 90]} name="Predicted Score" />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                  formatter={(value: number | string, name: string) => [value, name]}
                  labelFormatter={(_, payload) => {
                    const p = payload?.[0]?.payload
                    return p ? `${p.full_name} (${p.student_code}) · ${p.cluster_label}` : ''
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                {clusterGroups.map(
                  (grp) =>
                    grp.points.length > 0 && (
                      <Scatter key={grp.label} name={grp.label} data={grp.points} fill={grp.color} />
                    )
                )}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      {/* Cohort Comparison + Lowest Mastery Concepts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel title="Score Distribution & Cohort Comparison" subtitle="Predicted score bands across all enrolled students">
          <div className="h-64 w-full mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={score_distribution} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis dataKey="range" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" name="Students" radius={[5, 5, 0, 0]}>
                  {score_distribution.map((entry, idx) => (
                    <Cell
                      key={entry.range}
                      fill={idx === 0 ? '#F43F5E' : idx === 1 ? '#F59E0B' : idx === 2 ? '#0EA5E9' : '#10B981'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            {cohort_comparison.map((c) => (
              <div key={c.cohort} className="rounded-lg border border-slate-800 bg-navy-950/75 p-3">
                <div className="text-xs font-semibold text-slate-200 truncate">{c.cohort}</div>
                <div className="mt-1 flex items-center justify-between font-mono text-xs text-slate-400">
                  <span>{c.student_count} learners</span>
                  <span className="text-cyan-300 font-semibold">{c.avg_predicted_score}% avg</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title="Curriculum Bottleneck Concepts"
          subtitle="Lowest institutional mastery topics indicating curriculum calibration priorities"
        >
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={concept_analytics.slice(0, 8)}
                layout="vertical"
                margin={{ top: 4, right: 20, left: 10, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} stroke="#64748B" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={160}
                  stroke="#94A3B8"
                  fontSize={11}
                  tickFormatter={(v: string) => (v.length > 22 ? `${v.slice(0, 21)}...` : v)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="mean_mastery" fill="#F59E0B" radius={[0, 5, 5, 0]} name="Mean Mastery (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      {/* Priority Risk Roster */}
      <Panel
        title="Priority Early-Warning Learner Roster"
        subtitle="Highest predicted academic risk profiles requiring advisor intervention"
        rightSlot={
          <button
            type="button"
            onClick={() => navigate('/admin/students')}
            className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
          >
            Open Full Directory <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 pr-3">Student</th>
                <th className="py-2.5 px-3">Cohort</th>
                <th className="py-2.5 px-3">Persona Cluster</th>
                <th className="py-2.5 px-3">Attendance</th>
                <th className="py-2.5 px-3">Projected Score</th>
                <th className="py-2.5 pl-3">Risk Stratification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {priority_students.slice(0, 8).map((s) => (
                <tr
                  key={s.id}
                  onClick={() => navigate('/admin/students')}
                  className="cursor-pointer hover:bg-navy-800/50 transition-colors"
                >
                  <td className="py-2.5 pr-3">
                    <div className="font-semibold text-slate-100 flex items-center gap-2">
                      <GraduationCap className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                      {s.full_name}
                    </div>
                    <div className="font-mono text-[11px] text-slate-500">{s.student_code}</div>
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">{s.cohort.split(' - ')[0]}</td>
                  <td className="py-2.5 px-3 text-slate-300">{s.cluster_label}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-200">{s.attendance_rate}%</td>
                  <td className="py-2.5 px-3 font-mono font-semibold text-slate-100">{s.predicted_final_score}%</td>
                  <td className="py-2.5 pl-3">
                    <RiskBadge level={s.risk_level} score={s.risk_score} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}
