import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  Download,
  PlusCircle,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react'
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'
import { KpiCard, LoadingSkeleton, PageHeader, Panel, RiskBadge } from '../components/UiPrimitives'
import type { StudentDashboardPayload } from '../types'

export const StudentDashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const [data, setData] = useState<StudentDashboardPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [checkinOpen, setCheckinOpen] = useState(false)
  const [hours, setHours] = useState('2.5')
  const [sessions, setSessions] = useState('2')
  const [assignments, setAssignments] = useState('1')
  const [checkinBusy, setCheckinBusy] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  const loadDashboard = useCallback(async () => {
    try {
      setError(null)
      const res = await api.get<StudentDashboardPayload>('/students/me/dashboard')
      setData(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load student dashboard.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  const handleCheckin = async (e: React.FormEvent) => {
    e.preventDefault()
    setCheckinBusy(true)
    try {
      await api.post('/students/me/telemetry', {
        study_hours: parseFloat(hours),
        sessions_count: parseInt(sessions, 10),
        assignments_completed: parseInt(assignments, 10),
      })
      setCheckinOpen(false)
      setToast('Study telemetry recorded and predictive scores updated.')
      await loadDashboard()
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Unable to log study session.')
    } finally {
      setCheckinBusy(false)
    }
  }

  const handleCompleteResource = async (resourceId: number) => {
    try {
      await api.post(`/courses/resources/${resourceId}/interact`, { status: 'completed', rating: 5 })
      setToast('Module completed. Concept mastery and adaptive recommendations updated.')
      await loadDashboard()
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Could not update module.')
    }
  }

  const handleExportPdf = async () => {
    if (!data) return
    try {
      await api.download(
        `/reports/student/${data.profile.id}/pdf`,
        `Gayatri_AI_Report_${data.profile.student_code}.pdf`
      )
      setToast('PDF intelligence report downloaded.')
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'PDF export failed.')
    }
  }

  if (loading) return <LoadingSkeleton />
  if (error || !data) {
    return (
      <div className="enterprise-panel rounded-xl p-6 text-rose-300 border-rose-500/30">
        {error || 'Dashboard data unavailable.'}
      </div>
    )
  }

  const { profile, ml_intelligence, trajectory, enrollments, concept_masteries, recommendations, recent_submissions } =
    data
  const weakestConcepts = concept_masteries.slice(0, 8)

  return (
    <div className="space-y-6">
      {toast && (
        <div className="flex items-center justify-between rounded-xl border border-cyan-500/35 bg-cyan-500/10 px-4 py-3 text-xs text-cyan-200">
          <span>{toast}</span>
          <button type="button" onClick={() => setToast(null)} className="text-cyan-300 hover:text-white font-semibold">
            Dismiss
          </button>
        </div>
      )}

      <PageHeader
        title={`Welcome back, ${profile.full_name}`}
        subtitle={`${profile.student_code} · ${profile.cohort} · ${profile.program_track}`}
        actions={
          <>
            <button
              type="button"
              onClick={() => setCheckinOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg border border-cyan-500/35 bg-cyan-500/15 px-3.5 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/25 transition-colors"
            >
              <PlusCircle className="h-4 w-4" />
              Log Study Telemetry
            </button>
            <button
              type="button"
              onClick={handleExportPdf}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-navy-850 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500 transition-colors"
            >
              <Download className="h-4 w-4 text-emerald-400" />
              Export PDF Report
            </button>
          </>
        }
      />

      {/* Primary KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Projected Final Score"
          value={`${ml_intelligence.predicted_final_score.toFixed(1)}%`}
          subtext={`Cumulative GPA ${profile.current_gpa.toFixed(2)} / 4.00`}
          icon={TrendingUp}
          accent="cyan"
        />
        <KpiCard
          label="Concept Mastery Avg"
          value={`${profile.avg_concept_mastery.toFixed(1)}%`}
          subtext={`Across ${concept_masteries.length} tracked concepts`}
          icon={Target}
          accent="emerald"
        />
        <KpiCard
          label="Engagement & Attendance"
          value={`${profile.engagement_index.toFixed(0)} / 100`}
          subtext={`Attendance ${profile.attendance_rate.toFixed(1)}% · Timeliness ${profile.assignment_timeliness.toFixed(0)}%`}
          icon={Activity}
          accent="amber"
        />
        <div className="enterprise-panel rounded-xl p-4 sm:p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Predictive Risk & Persona</span>
            <AlertTriangle className="h-4 w-4 text-slate-400" />
          </div>
          <div className="mt-2 flex items-center justify-between gap-2">
            <RiskBadge level={ml_intelligence.risk_level} score={ml_intelligence.risk_score} />
          </div>
          <div className="mt-2.5 text-xs text-slate-300 font-medium truncate">
            Cluster: <span className="text-cyan-300">{ml_intelligence.cluster.cluster_label}</span>
          </div>
        </div>
      </div>

      {/* Trajectory Forecast + Explainable Risk Drivers */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Panel
          title="10-Week Performance Trajectory & 4-Week Ridge Forecast"
          subtitle="Observed weekly quiz scores with damped projection and 90% confidence band"
          className="lg:col-span-2"
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={trajectory} margin={{ top: 10, right: 16, left: -12, bottom: 0 }}>
                <defs>
                  <linearGradient id="bandFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                <XAxis dataKey="week_label" stroke="#64748B" fontSize={11} />
                <YAxis domain={[35, 100]} stroke="#64748B" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="upper_bound"
                  stroke="none"
                  fill="url(#bandFill)"
                  name="Upper Forecast Bound"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="actual_score"
                  stroke="#22D3EE"
                  strokeWidth={2.5}
                  dot={{ r: 3.5, fill: '#22D3EE' }}
                  name="Observed Score (%)"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="projected_score"
                  stroke="#10B981"
                  strokeWidth={2.5}
                  strokeDasharray="6 4"
                  dot={{ r: 3.5, fill: '#10B981' }}
                  name="Projected Score (%)"
                  connectNulls
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title="Predictive Feature Drivers"
          subtitle="Local model attribution vs institutional cohort averages"
        >
          <div className="space-y-3.5">
            {ml_intelligence.drivers.map((d) => {
              const isRisk = d.effect === 'risk_increasing'
              const isProt = d.effect === 'protective'
              return (
                <div key={d.feature} className="rounded-lg border border-slate-800/80 bg-navy-950/70 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-slate-200">{d.label}</span>
                    <span
                      className={`text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full ${
                        isRisk
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : isProt
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {isRisk ? 'Risk Factor' : isProt ? 'Protective' : 'Neutral'}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between font-mono text-xs text-slate-400">
                    <span>
                      Yours: <strong className="text-slate-100">{d.student_value}</strong>
                    </span>
                    <span>Cohort Mean: {d.cohort_mean}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </Panel>
      </div>

      {/* Concept Mastery Gaps & Adaptive Recommendations */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel
          title="Concept Mastery Diagnostic (Lowest Priority Topics)"
          subtitle="Live Bayesian/EWMA mastery updated on assessments & resource completions"
          rightSlot={
            <button
              type="button"
              onClick={() => navigate('/analytics')}
              className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              Full Matrix <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          }
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={weakestConcepts}
                layout="vertical"
                margin={{ top: 4, right: 20, left: 10, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} stroke="#64748B" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="concept_name"
                  width={150}
                  stroke="#94A3B8"
                  fontSize={11}
                  tickFormatter={(v: string) => (v.length > 21 ? `${v.slice(0, 20)}...` : v)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="mastery_score" fill="#22D3EE" radius={[0, 5, 5, 0]} name="Mastery (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title="Intelligent Learning Recommendations"
          subtitle="Ranked by mastery deficit urgency, prerequisite readiness, and TF-IDF fit"
          rightSlot={
            <button
              type="button"
              onClick={() => navigate('/courses')}
              className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              All Modules <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          }
        >
          <div className="space-y-3">
            {recommendations.slice(0, 4).map((rec) => (
              <div
                key={rec.resource_id}
                className="rounded-xl border border-slate-800/90 bg-navy-950/75 p-3.5 hover:border-cyan-500/35 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-[10px] font-semibold rounded bg-cyan-500/15 text-cyan-300 px-1.5 py-0.5">
                        {rec.course_code}
                      </span>
                      <span className="text-[11px] text-amber-300 font-medium">{rec.prerequisite_status}</span>
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Clock className="h-3 w-3" /> {rec.estimated_minutes}m
                      </span>
                    </div>
                    <h3 className="mt-1 text-sm font-semibold text-slate-100 truncate">{rec.title}</h3>
                    <p className="mt-1 text-xs text-slate-400 line-clamp-2">{rec.rationale}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="font-mono text-xs font-semibold text-emerald-400">{rec.match_score}% match</div>
                    {rec.interaction_status === 'completed' ? (
                      <span className="mt-2 inline-flex items-center gap-1 text-[11px] text-emerald-300">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Done
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleCompleteResource(rec.resource_id)}
                        className="mt-2 rounded-md border border-emerald-500/35 bg-emerald-500/15 px-2.5 py-1 text-[11px] font-semibold text-emerald-300 hover:bg-emerald-500/25 transition-colors"
                      >
                        Mark Complete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* Active Courses & Recent Assessments */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel title="Enrolled Course Progress" subtitle="Active curriculum track completion and current standings">
          <div className="space-y-3">
            {enrollments.map((enr) => (
              <div
                key={enr.course_id}
                onClick={() => navigate('/courses')}
                className="cursor-pointer rounded-xl border border-slate-800 bg-navy-950/70 p-3.5 hover:border-cyan-500/35 transition-colors"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                      <span className="font-mono text-xs text-cyan-300">{enr.course_code}</span>
                      <span className="text-sm font-semibold text-slate-100 truncate">{enr.course_title}</span>
                    </div>
                    <div className="mt-1 text-xs text-slate-400">
                      {enr.instructor_name} · {enr.modules_completed}/{enr.modules_total} modules
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="font-mono text-sm font-semibold text-slate-100">{enr.current_grade.toFixed(1)}%</div>
                    <div className="text-[11px] text-slate-400">Grade</div>
                  </div>
                </div>
                <div className="mt-2.5 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400"
                    style={{ width: `${Math.min(100, enr.progress_pct)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title="Recent Assessment Evaluations"
          subtitle="Automated mastery-linked evaluation history"
          rightSlot={
            <button
              type="button"
              onClick={() => navigate('/assessments')}
              className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              Take Assessment <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="py-2.5 pr-3">Assessment</th>
                  <th className="py-2.5 px-3">Score</th>
                  <th className="py-2.5 px-3">Result</th>
                  <th className="py-2.5 pl-3 text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {recent_submissions.map((sub) => (
                  <tr key={sub.submission_id} className="hover:bg-navy-800/40">
                    <td className="py-2.5 pr-3 font-medium text-slate-200">{sub.assessment_title}</td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-slate-100">{sub.score_pct.toFixed(1)}%</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          sub.passed
                            ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                            : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        }`}
                      >
                        <Award className="h-3 w-3" />
                        {sub.passed ? 'Passed' : 'Review'}
                      </span>
                    </td>
                    <td className="py-2.5 pl-3 text-right font-mono text-slate-400">
                      {new Date(sub.submitted_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 rounded-lg border border-slate-800 bg-navy-950/70 p-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <Sparkles className="h-4 w-4 text-cyan-400 shrink-0" />
              <span>Need targeted tutoring on weak concepts?</span>
            </div>
            <button
              type="button"
              onClick={() => navigate('/assistant')}
              className="rounded-md bg-cyan-500/15 border border-cyan-500/30 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/25 shrink-0"
            >
              Ask Assistant
            </button>
          </div>
        </Panel>
      </div>

      {/* Study Telemetry Check-In Modal */}
      {checkinOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="enterprise-panel w-full max-w-md rounded-2xl p-6">
            <h3 className="text-lg font-bold text-slate-100">Log Weekly Study Telemetry</h3>
            <p className="mt-1 text-xs text-slate-400">
              Record completed study sessions to update your engagement index and recalculate predictive risk.
            </p>
            <form onSubmit={handleCheckin} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Additional Study Hours</label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="40"
                  required
                  value={hours}
                  onChange={(e) => setHours(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-sm font-mono text-slate-100"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Focus Sessions</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    required
                    value={sessions}
                    onChange={(e) => setSessions(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-sm font-mono text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Tasks Completed</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    required
                    value={assignments}
                    onChange={(e) => setAssignments(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-sm font-mono text-slate-100"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setCheckinOpen(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-navy-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={checkinBusy}
                  className="rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-60"
                >
                  {checkinBusy ? 'Updating...' : 'Record Telemetry'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
