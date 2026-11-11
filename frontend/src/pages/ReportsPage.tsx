import React, { useEffect, useState } from 'react'
import { Download, FileSpreadsheet, FileText, ShieldCheck } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { LoadingSkeleton, PageHeader, Panel } from '../components/UiPrimitives'

interface StudentOption {
  id: number
  student_code: string
  full_name: string
  cohort: string
  risk_level: string
  predicted_final_score: number
}

export const ReportsPage: React.FC = () => {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [students, setStudents] = useState<StudentOption[]>([])
  const [selectedStudentId, setSelectedStudentId] = useState<number>(user?.student_profile_id || 0)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState<string | null>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)

  useEffect(() => {
    if (isAdmin) {
      api
        .get<{ students: StudentOption[] }>('/admin/students?limit=150')
        .then((res) => {
          setStudents(res.students)
          if (res.students.length > 0) setSelectedStudentId(res.students[0].id)
        })
        .finally(() => setLoading(false))
    } else {
      if (user?.student_profile_id) setSelectedStudentId(user.student_profile_id)
      setLoading(false)
    }
  }, [isAdmin, user])

  const triggerDownload = async (key: string, endpoint: string, fallbackName: string) => {
    setDownloading(key)
    setStatusMsg(null)
    try {
      await api.download(endpoint, fallbackName)
      setStatusMsg(`Exported ${fallbackName} successfully.`)
    } catch (err) {
      setStatusMsg(err instanceof Error ? err.message : 'Download failed.')
    } finally {
      setDownloading(null)
    }
  }

  if (loading) return <LoadingSkeleton rows={2} />

  const chosenStudent = students.find((s) => s.id === selectedStudentId)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Exportable Reports & Intelligence Transcripts"
        subtitle="Generate publication-ready PDF performance briefs with embedded charts and structured CSV datasets"
      />

      {statusMsg && (
        <div className="rounded-xl border border-emerald-500/35 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-200 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {isAdmin && (
          <Panel
            title="Executive Institutional Cohort Reports"
            subtitle="Complete cross-cohort risk stratification, K-Means segmentation, and model validation metrics"
          >
            <div className="space-y-4">
              <div className="rounded-xl border border-slate-800 bg-navy-950/75 p-4 text-xs text-slate-300 leading-relaxed">
                Includes institutional KPIs, cross-validated Risk Classifier & Score Regressor performance metrics,
                embedded Matplotlib risk & PCA cluster plots, priority at-risk roster, and curriculum bottleneck rankings.
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={downloading !== null}
                  onClick={() =>
                    triggerDownload('cohort-pdf', '/reports/cohort/pdf', 'Gayatri_AI_Executive_Cohort_Report.pdf')
                  }
                  className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-4 py-2.5 text-xs font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-60"
                >
                  <FileText className="h-4 w-4" />
                  {downloading === 'cohort-pdf' ? 'Rendering PDF...' : 'Download Executive Cohort PDF'}
                </button>
                <button
                  type="button"
                  disabled={downloading !== null}
                  onClick={() =>
                    triggerDownload('cohort-csv', '/reports/cohort/csv', 'Gayatri_AI_Cohort_Telemetry.csv')
                  }
                  className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/35 bg-emerald-500/15 px-4 py-2.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/25 disabled:opacity-60"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  {downloading === 'cohort-csv' ? 'Exporting CSV...' : 'Export Cohort Telemetry CSV'}
                </button>
              </div>
            </div>
          </Panel>
        )}

        <Panel
          title={isAdmin ? 'Individual Learner Intelligence Transcript' : 'Personal Academic Performance Report'}
          subtitle="Formatted PDF with trajectory forecast chart, feature drivers, and concept mastery CSV"
          className={!isAdmin ? 'lg:col-span-2' : ''}
        >
          <div className="space-y-4">
            {isAdmin && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Select Student Profile</label>
                <select
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-xs text-slate-100 focus:border-cyan-500 focus:outline-none"
                >
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.student_code} — {s.full_name} ({s.risk_level.toUpperCase()} Risk · {s.predicted_final_score}%)
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="rounded-xl border border-slate-800 bg-navy-950/75 p-4 text-xs text-slate-300 leading-relaxed">
              Includes learner summary metrics, 10-week score trajectory & 4-week Ridge forecast chart with confidence
              interval, predictive risk drivers, adaptive study recommendations, and assessment transcript.
              {chosenStudent && (
                <div className="mt-2 font-mono text-cyan-300">
                  Selected: {chosenStudent.full_name} ({chosenStudent.student_code})
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                disabled={!selectedStudentId || downloading !== null}
                onClick={() =>
                  triggerDownload(
                    'student-pdf',
                    `/reports/student/${selectedStudentId}/pdf`,
                    `Gayatri_AI_Student_Report_${selectedStudentId}.pdf`
                  )
                }
                className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-4 py-2.5 text-xs font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-60"
              >
                <Download className="h-4 w-4" />
                {downloading === 'student-pdf' ? 'Rendering PDF...' : 'Download Performance Report PDF'}
              </button>
              <button
                type="button"
                disabled={!selectedStudentId || downloading !== null}
                onClick={() =>
                  triggerDownload(
                    'student-csv',
                    `/reports/student/${selectedStudentId}/csv`,
                    `Gayatri_AI_Mastery_${selectedStudentId}.csv`
                  )
                }
                className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/35 bg-emerald-500/15 px-4 py-2.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/25 disabled:opacity-60"
              >
                <FileSpreadsheet className="h-4 w-4" />
                {downloading === 'student-csv' ? 'Exporting CSV...' : 'Download Concept Mastery CSV'}
              </button>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  )
}
