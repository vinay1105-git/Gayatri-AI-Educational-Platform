import React, { useCallback, useEffect, useState } from 'react'
import { Download, Eye, Plus, Search, ShieldAlert, X } from 'lucide-react'
import { api } from '../api/client'
import { LoadingSkeleton, PageHeader, Panel, RiskBadge } from '../components/UiPrimitives'
import type { StudentDashboardPayload } from '../types'

interface AdminStudentRow {
  id: number
  student_code: string
  full_name: string
  email: string
  avatar_initials: string
  cohort: string
  program_track: string
  semester: number
  attendance_rate: number
  engagement_index: number
  current_gpa: number
  predicted_final_score: number
  risk_score: number
  risk_level: 'low' | 'moderate' | 'high'
  cluster_label: string
}

interface InterventionRow {
  id: number
  student_id: number
  student_code: string
  student_name: string
  student_risk_level: string
  intervention_type: string
  priority: string
  notes: string
  status: string
  created_by_name: string
  created_at: string
}

interface AuditLogRow {
  id: number
  user_email: string
  action: string
  resource_type: string
  details: string
  ip_address: string
  created_at: string
}

export const AdminStudentsPage: React.FC = () => {
  const [tab, setTab] = useState<'directory' | 'interventions' | 'audit'>('directory')
  const [students, setStudents] = useState<AdminStudentRow[]>([])
  const [interventions, setInterventions] = useState<InterventionRow[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLogRow[]>([])
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('')
  const [cohortFilter, setCohortFilter] = useState('')

  const [inspected, setInspected] = useState<StudentDashboardPayload | null>(null)
  const [ivModalStudent, setIvModalStudent] = useState<AdminStudentRow | null>(null)
  const [ivType, setIvType] = useState('Academic Coaching')
  const [ivPriority, setIvPriority] = useState<'high' | 'medium' | 'low'>('high')
  const [ivNotes, setIvNotes] = useState('')
  const [toast, setToast] = useState<string | null>(null)

  const loadDirectory = useCallback(async () => {
    const params = new URLSearchParams()
    if (search.trim()) params.set('search', search.trim())
    if (riskFilter) params.set('risk_level', riskFilter)
    if (cohortFilter) params.set('cohort', cohortFilter)
    params.set('limit', '120')
    const res = await api.get<{ students: AdminStudentRow[] }>(`/admin/students?${params.toString()}`)
    setStudents(res.students)
  }, [search, riskFilter, cohortFilter])

  const loadInterventions = useCallback(async () => {
    const res = await api.get<{ interventions: InterventionRow[] }>('/admin/interventions')
    setInterventions(res.interventions)
  }, [])

  const loadAuditLogs = useCallback(async () => {
    const res = await api.get<{ logs: AuditLogRow[] }>('/admin/audit-logs?limit=50')
    setAuditLogs(res.logs)
  }, [])

  useEffect(() => {
    Promise.all([loadDirectory(), loadInterventions(), loadAuditLogs()]).finally(() => setLoading(false))
  }, [loadDirectory, loadInterventions, loadAuditLogs])

  const inspectStudent = async (studentId: number) => {
    const detail = await api.get<StudentDashboardPayload>(`/students/${studentId}/dashboard`)
    setInspected(detail)
  }

  const createIntervention = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ivModalStudent) return
    await api.post('/admin/interventions', {
      student_id: ivModalStudent.id,
      intervention_type: ivType,
      priority: ivPriority,
      notes: ivNotes,
    })
    setIvModalStudent(null)
    setIvNotes('')
    setToast(`Intervention logged for ${ivModalStudent.full_name}.`)
    await Promise.all([loadInterventions(), loadAuditLogs()])
  }

  const updateInterventionStatus = async (id: number, status: 'open' | 'in_progress' | 'resolved') => {
    await api.patch(`/admin/interventions/${id}`, { status })
    setToast(`Intervention #${id} updated to ${status}.`)
    await loadInterventions()
  }

  if (loading) return <LoadingSkeleton />

  return (
    <div className="space-y-6">
      {toast && (
        <div className="flex items-center justify-between rounded-xl border border-emerald-500/35 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-200">
          <span>{toast}</span>
          <button type="button" onClick={() => setToast(null)} className="font-semibold text-emerald-300">
            Dismiss
          </button>
        </div>
      )}

      <PageHeader
        title="Student Directory & Intervention Console"
        subtitle="Search learner profiles, inspect individual ML attributions, manage outreach cases, and audit platform logs"
        actions={
          <div className="flex rounded-lg border border-slate-800 bg-navy-900 p-1">
            {(['directory', 'interventions', 'audit'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`rounded-md px-3 py-1.5 text-xs font-semibold capitalize transition-colors ${
                  tab === t ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t === 'directory'
                  ? `Students (${students.length})`
                  : t === 'interventions'
                  ? `Interventions (${interventions.length})`
                  : 'Audit Trail'}
              </button>
            ))}
          </div>
        }
      />

      {tab === 'directory' && (
        <>
          <Panel>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search name, email, or GAI code..."
                  className="w-full rounded-lg border border-slate-700/80 bg-navy-950 pl-9 pr-3 py-2 text-xs text-slate-100 focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="rounded-lg border border-slate-700/80 bg-navy-950 px-3 py-2 text-xs text-slate-100"
              >
                <option value="">All Risk Tiers</option>
                <option value="high">High Risk</option>
                <option value="moderate">Moderate Risk</option>
                <option value="low">Low Risk</option>
              </select>
              <select
                value={cohortFilter}
                onChange={(e) => setCohortFilter(e.target.value)}
                className="rounded-lg border border-slate-700/80 bg-navy-950 px-3 py-2 text-xs text-slate-100"
              >
                <option value="">All Cohorts</option>
                <option value="Fall 2026 - AI Engineering">Fall 2026 - AI Engineering</option>
                <option value="Spring 2026 - Applied ML">Spring 2026 - Applied ML</option>
                <option value="Summer 2026 - Data Systems">Summer 2026 - Data Systems</option>
                <option value="Fall 2026 - MLOps Track">Fall 2026 - MLOps Track</option>
              </select>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                    <th className="py-2.5 pr-3">Learner</th>
                    <th className="py-2.5 px-3">Cohort</th>
                    <th className="py-2.5 px-3">Cluster Persona</th>
                    <th className="py-2.5 px-3">GPA / Att</th>
                    <th className="py-2.5 px-3">Pred Score</th>
                    <th className="py-2.5 px-3">Risk</th>
                    <th className="py-2.5 pl-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70">
                  {students.map((s) => (
                    <tr key={s.id} className="hover:bg-navy-800/40">
                      <td className="py-2.5 pr-3">
                        <div className="font-semibold text-slate-100">{s.full_name}</div>
                        <div className="font-mono text-[11px] text-slate-500">
                          {s.student_code} · {s.email}
                        </div>
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">{s.cohort.split(' - ')[0]}</td>
                      <td className="py-2.5 px-3 text-slate-300">{s.cluster_label}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-200">
                        {s.current_gpa.toFixed(2)} / {s.attendance_rate}%
                      </td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-cyan-300">{s.predicted_final_score}%</td>
                      <td className="py-2.5 px-3">
                        <RiskBadge level={s.risk_level} score={s.risk_score} />
                      </td>
                      <td className="py-2.5 pl-3 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => inspectStudent(s.id)}
                            className="inline-flex items-center gap-1 rounded-md border border-cyan-500/35 bg-cyan-500/15 px-2.5 py-1 text-[11px] font-semibold text-cyan-200 hover:bg-cyan-500/25"
                          >
                            <Eye className="h-3 w-3" /> Inspect
                          </button>
                          <button
                            type="button"
                            onClick={() => setIvModalStudent(s)}
                            className="inline-flex items-center gap-1 rounded-md border border-amber-500/35 bg-amber-500/15 px-2.5 py-1 text-[11px] font-semibold text-amber-200 hover:bg-amber-500/25"
                          >
                            <Plus className="h-3 w-3" /> Intervene
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}

      {tab === 'interventions' && (
        <Panel title="Academic Intervention Registry" subtitle="Track advisor outreach cases and resolution lifecycle">
          <div className="space-y-3">
            {interventions.map((iv) => (
              <div
                key={iv.id}
                className="rounded-xl border border-slate-800 bg-navy-950/75 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <ShieldAlert className="h-4 w-4 text-amber-400" />
                    <span className="font-semibold text-sm text-slate-100">{iv.student_name}</span>
                    <span className="font-mono text-xs text-slate-400">({iv.student_code})</span>
                    <span className="rounded bg-cyan-500/15 border border-cyan-500/30 px-2 py-0.5 text-[10px] font-semibold text-cyan-300">
                      {iv.intervention_type}
                    </span>
                    <span className="uppercase text-[10px] font-bold text-amber-300">{iv.priority} priority</span>
                  </div>
                  <p className="mt-1.5 text-xs text-slate-300">{iv.notes}</p>
                  <div className="mt-1 text-[11px] text-slate-500">
                    Logged by {iv.created_by_name} on {new Date(iv.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {(['open', 'in_progress', 'resolved'] as const).map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => updateInterventionStatus(iv.id, st)}
                      className={`rounded-md px-2.5 py-1 text-[11px] font-semibold capitalize border transition-colors ${
                        iv.status === st
                          ? 'border-emerald-400 bg-emerald-500/20 text-emerald-200'
                          : 'border-slate-700 bg-navy-900 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {st.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {tab === 'audit' && (
        <Panel title="Enterprise Compliance & Security Audit Log" subtitle="Immutable operational log of logins, assessments, interventions, and exports">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <th className="py-2 pr-3">Timestamp</th>
                  <th className="py-2 px-3">Actor</th>
                  <th className="py-2 px-3">Action</th>
                  <th className="py-2 px-3">Details</th>
                  <th className="py-2 pl-3 text-right">IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-navy-800/40">
                    <td className="py-2 pr-3 font-mono text-[11px] text-slate-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 font-mono text-slate-300">{log.user_email}</td>
                    <td className="py-2 px-3 font-mono text-cyan-300">{log.action}</td>
                    <td className="py-2 px-3 text-slate-300">{log.details}</td>
                    <td className="py-2 pl-3 text-right font-mono text-slate-500">{log.ip_address}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* Student Deep-Dive Inspector Modal */}
      {inspected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="enterprise-panel w-full max-w-3xl rounded-2xl p-6 max-h-[90vh] overflow-y-auto space-y-5">
            <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <div className="font-mono text-xs text-cyan-400">{inspected.profile.student_code}</div>
                <h3 className="text-xl font-bold text-slate-100">{inspected.profile.full_name}</h3>
                <div className="text-xs text-slate-400 mt-0.5">
                  {inspected.profile.cohort} · {inspected.profile.program_track}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    api.download(
                      `/reports/student/${inspected.profile.id}/pdf`,
                      `Gayatri_AI_Report_${inspected.profile.student_code}.pdf`
                    )
                  }
                  className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/35 bg-cyan-500/15 px-3 py-1.5 text-xs font-semibold text-cyan-200"
                >
                  <Download className="h-3.5 w-3.5" /> PDF Report
                </button>
                <button
                  type="button"
                  onClick={() => setInspected(null)}
                  className="rounded-lg border border-slate-700 p-1.5 text-slate-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="rounded-xl border border-slate-800 bg-navy-950/80 p-3">
                <div className="text-[10px] uppercase text-slate-400">Projected Score</div>
                <div className="font-mono text-lg font-bold text-cyan-300 mt-1">
                  {inspected.ml_intelligence.predicted_final_score.toFixed(1)}%
                </div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-navy-950/80 p-3">
                <div className="text-[10px] uppercase text-slate-400">Risk Index</div>
                <div className="mt-1">
                  <RiskBadge level={inspected.ml_intelligence.risk_level} score={inspected.ml_intelligence.risk_score} />
                </div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-navy-950/80 p-3">
                <div className="text-[10px] uppercase text-slate-400">Attendance</div>
                <div className="font-mono text-lg font-bold text-slate-100 mt-1">
                  {inspected.profile.attendance_rate}%
                </div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-navy-950/80 p-3">
                <div className="text-[10px] uppercase text-slate-400">Cluster Persona</div>
                <div className="text-xs font-semibold text-emerald-300 mt-1.5">
                  {inspected.ml_intelligence.cluster.cluster_label}
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Top Predictive Feature Attributions
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {inspected.ml_intelligence.drivers.map((d) => (
                  <div key={d.feature} className="rounded-lg border border-slate-800 bg-navy-950/75 p-3 text-xs">
                    <div className="flex justify-between">
                      <span className="font-semibold text-slate-200">{d.label}</span>
                      <span
                        className={
                          d.effect === 'risk_increasing'
                            ? 'text-rose-300'
                            : d.effect === 'protective'
                            ? 'text-emerald-300'
                            : 'text-slate-400'
                        }
                      >
                        {d.effect === 'risk_increasing' ? 'Risk Driver' : 'Protective'}
                      </span>
                    </div>
                    <div className="mt-1 font-mono text-slate-400">
                      Student: {d.student_value} · Cohort: {d.cohort_mean}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Weakest Concept Masteries
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {inspected.concept_masteries.slice(0, 6).map((cm) => (
                  <div key={cm.concept_id} className="flex items-center justify-between rounded-lg border border-slate-800 bg-navy-950/70 px-3 py-2 text-xs">
                    <span className="text-slate-200 truncate">{cm.concept_name}</span>
                    <span className="font-mono font-semibold text-amber-300 ml-2">{cm.mastery_score}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Intervention Modal */}
      {ivModalStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="enterprise-panel w-full max-w-md rounded-2xl p-6">
            <h3 className="text-lg font-bold text-slate-100">Log Academic Intervention</h3>
            <p className="mt-1 text-xs text-slate-400">
              Target Learner: <strong className="text-slate-200">{ivModalStudent.full_name}</strong> ({ivModalStudent.student_code})
            </p>
            <form onSubmit={createIntervention} className="mt-4 space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Intervention Strategy</label>
                <select
                  value={ivType}
                  onChange={(e) => setIvType(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                >
                  <option value="Academic Coaching">Academic Coaching</option>
                  <option value="Prerequisite Review Plan">Prerequisite Review Plan</option>
                  <option value="Workload Calibration">Workload Calibration</option>
                  <option value="Peer Mentorship">Peer Mentorship</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Priority</label>
                <select
                  value={ivPriority}
                  onChange={(e) => setIvPriority(e.target.value as 'high' | 'medium' | 'low')}
                  className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                >
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Advisor Action Notes</label>
                <textarea
                  required
                  minLength={5}
                  rows={3}
                  value={ivNotes}
                  onChange={(e) => setIvNotes(e.target.value)}
                  placeholder="Specific outreach plan, milestone adjustments, or prerequisite modules assigned..."
                  className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIvModalStudent(null)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-slate-300"
                >
                  Cancel
                </button>
                <button type="submit" className="rounded-lg bg-amber-500 px-4 py-2 font-semibold text-slate-950">
                  Save Intervention
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
