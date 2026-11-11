import React, { useCallback, useEffect, useState } from 'react'
import {
  Activity,
  AlertCircle,
  Award,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  Plus,
  Timer,
  X,
  XCircle,
} from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { LoadingSkeleton, PageHeader, Panel } from '../components/UiPrimitives'
import type { AssessmentSummary, CourseItem } from '../types'

interface AssessmentQuestion {
  id: number
  concept_id: number
  concept_name: string
  prompt: string
  options: string[]
  difficulty: string
  points: number
  correct_index?: number
  explanation?: string
}

interface AssessmentDetail {
  id: number
  course_code: string
  course_title: string
  title: string
  assessment_type: string
  description: string
  duration_minutes: number
  passing_score: number
  total_points: number
  questions: AssessmentQuestion[]
}

interface GradedResult {
  submission_id: number
  assessment_title: string
  score_pct: number
  points_earned: number
  points_possible: number
  correct_count: number
  total_questions: number
  passed: boolean
  passing_score: number
  updated_prediction?: {
    predicted_final_score: number
    risk_score: number
    risk_level: string
  }
  items: Array<{
    question_id: number
    prompt: string
    concept_name: string
    selected_index: number
    correct_index: number
    options: string[]
    is_correct: boolean
    explanation: string
    updated_concept_mastery?: number
  }>
}

interface PsychometricsData {
  assessment_id: number
  title: string
  submissions_count: number
  mean_score: number
  median_score: number
  std_dev: number
  pass_rate: number
  items: Array<{
    question_id: number
    prompt: string
    concept_name: string
    difficulty_tag: string
    attempts: number
    difficulty_p_value: number
    discrimination_index: number
    calibration_status: string
  }>
}

export const AssessmentsPage: React.FC = () => {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [assessments, setAssessments] = useState<AssessmentSummary[]>([])
  const [loading, setLoading] = useState(true)

  // Active assessment taking / reviewing state
  const [activeAssessment, setActiveAssessment] = useState<AssessmentDetail | null>(null)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [elapsedSec, setElapsedSec] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [gradedResult, setGradedResult] = useState<GradedResult | null>(null)

  // Admin psychometrics & builder state
  const [psychometrics, setPsychometrics] = useState<PsychometricsData | null>(null)
  const [builderOpen, setBuilderOpen] = useState(false)
  const [courses, setCourses] = useState<CourseItem[]>([])
  const [concepts, setConcepts] = useState<Array<{ id: number; code: string; name: string; course_id: number }>>([])
  const [newTitle, setNewTitle] = useState('')
  const [newCourseId, setNewCourseId] = useState<number>(0)
  const [newDesc, setNewDesc] = useState('')
  const [qConceptId, setQConceptId] = useState<number>(0)
  const [qPrompt, setQPrompt] = useState('')
  const [qOptions, setQOptions] = useState(['', '', '', ''])
  const [qCorrect, setQCorrect] = useState(0)
  const [qExplanation, setQExplanation] = useState('')
  const [qDifficulty, setQDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium')
  const [builderError, setBuilderError] = useState<string | null>(null)
  const [builderSuccess, setBuilderSuccess] = useState<string | null>(null)

  const loadAssessments = useCallback(async () => {
    try {
      const res = await api.get<{ assessments: AssessmentSummary[] }>('/assessments')
      setAssessments(res.assessments)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAssessments()
  }, [loadAssessments])

  useEffect(() => {
    if (!activeAssessment || gradedResult) return
    const timer = window.setInterval(() => {
      setElapsedSec((prev) => prev + 1)
    }, 1000)
    return () => window.clearInterval(timer)
  }, [activeAssessment, gradedResult])

  const startAssessment = async (assessmentId: number) => {
    const detail = await api.get<AssessmentDetail>(`/assessments/${assessmentId}`)
    setActiveAssessment(detail)
    setAnswers({})
    setElapsedSec(0)
    setGradedResult(null)
    setPsychometrics(null)
  }

  const viewPastSubmission = async (submissionId: number) => {
    const res = await api.get<GradedResult>(`/assessments/submissions/${submissionId}`)
    setGradedResult(res)
    setActiveAssessment(null)
  }

  const handleSubmitAssessment = async () => {
    if (!activeAssessment) return
    setSubmitting(true)
    try {
      const res = await api.post<GradedResult>(`/assessments/${activeAssessment.id}/submit`, {
        answers,
        time_spent_seconds: Math.max(15, elapsedSec),
      })
      setGradedResult(res)
      await loadAssessments()
    } finally {
      setSubmitting(false)
    }
  }

  const openPsychometrics = async (assessmentId: number) => {
    const data = await api.get<PsychometricsData>(`/assessments/${assessmentId}/psychometrics`)
    setPsychometrics(data)
    setActiveAssessment(null)
    setGradedResult(null)
  }

  const openBuilder = async () => {
    const [cRes, kRes] = await Promise.all([
      api.get<{ courses: CourseItem[] }>('/courses'),
      api.get<{ concepts: Array<{ id: number; code: string; name: string; course_id: number }> }>(
        '/assessments/concepts/catalog'
      ),
    ])
    setCourses(cRes.courses)
    setConcepts(kRes.concepts)
    if (cRes.courses.length > 0) {
      const cid = cRes.courses[0].id
      setNewCourseId(cid)
      const matching = kRes.concepts.filter((c) => c.course_id === cid)
      if (matching.length > 0) setQConceptId(matching[0].id)
    }
    setBuilderError(null)
    setBuilderSuccess(null)
    setBuilderOpen(true)
  }

  const handleCreateAssessment = async (e: React.FormEvent) => {
    e.preventDefault()
    setBuilderError(null)
    try {
      await api.post('/assessments', {
        course_id: newCourseId,
        title: newTitle,
        assessment_type: 'Module Exam',
        description: newDesc,
        duration_minutes: 15,
        passing_score: 70,
        questions: [
          {
            concept_id: qConceptId,
            prompt: qPrompt,
            options: qOptions,
            correct_index: qCorrect,
            explanation: qExplanation,
            difficulty: qDifficulty,
            points: 20,
          },
        ],
      })
      setBuilderSuccess('Assessment published and integrated into concept tracking.')
      setBuilderOpen(false)
      setNewTitle('')
      setNewDesc('')
      setQPrompt('')
      setQOptions(['', '', '', ''])
      setQExplanation('')
      await loadAssessments()
    } catch (err) {
      setBuilderError(err instanceof Error ? err.message : 'Unable to create assessment.')
    }
  }

  if (loading) return <LoadingSkeleton />

  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isAdmin ? 'Assessment Studio & Psychometrics' : 'Assessment & Evaluation Center'}
        subtitle={
          isAdmin
            ? 'Author concept-mapped evaluations and inspect item difficulty and discrimination analytics'
            : 'Complete interactive evaluations with instant grading, explanations, and live ML mastery updates'
        }
        actions={
          isAdmin ? (
            <button
              type="button"
              onClick={openBuilder}
              className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-3.5 py-2 text-xs font-semibold text-slate-950 hover:bg-cyan-400"
            >
              <Plus className="h-4 w-4" />
              Create Assessment
            </button>
          ) : undefined
        }
      />

      {builderSuccess && (
        <div className="rounded-xl border border-emerald-500/35 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-200">
          {builderSuccess}
        </div>
      )}

      {/* Active Assessment Runner */}
      {activeAssessment && !gradedResult && (
        <Panel
          title={`${activeAssessment.course_code} · ${activeAssessment.title}`}
          subtitle={`Passing threshold: ${activeAssessment.passing_score}% · ${activeAssessment.questions.length} items`}
          rightSlot={
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 font-mono text-xs text-cyan-300">
                <Timer className="h-3.5 w-3.5" />
                {formatDuration(elapsedSec)}
              </span>
              <button
                type="button"
                onClick={() => setActiveAssessment(null)}
                className="rounded-lg border border-slate-700 p-1.5 text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          }
        >
          <div className="space-y-5">
            {activeAssessment.questions.map((q, qIdx) => (
              <div key={q.id} className="rounded-xl border border-slate-800 bg-navy-950/75 p-4 sm:p-5">
                <div className="flex items-center justify-between gap-2 text-xs mb-2">
                  <span className="font-mono text-cyan-300">
                    Question {qIdx + 1} / {activeAssessment.questions.length} · {q.concept_name}
                  </span>
                  <span className="uppercase text-[10px] font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/25 rounded px-2 py-0.5">
                    {q.difficulty} · {q.points} pts
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-100 leading-relaxed">{q.prompt}</p>
                <div className="mt-3.5 grid grid-cols-1 gap-2">
                  {q.options.map((opt, optIdx) => {
                    const selected = answers[q.id] === optIdx
                    return (
                      <button
                        key={optIdx}
                        type="button"
                        onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: optIdx }))}
                        className={`flex items-center gap-3 rounded-lg border px-3.5 py-2.5 text-left text-xs transition-colors ${
                          selected
                            ? 'border-cyan-400 bg-cyan-500/15 text-cyan-100'
                            : 'border-slate-800 bg-navy-900/70 text-slate-300 hover:border-slate-600'
                        }`}
                      >
                        <span
                          className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border font-mono text-[11px] ${
                            selected ? 'border-cyan-400 bg-cyan-400 text-slate-950 font-bold' : 'border-slate-600 text-slate-400'
                          }`}
                        >
                          {String.fromCharCode(65 + optIdx)}
                        </span>
                        <span>{opt}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}

            <div className="flex items-center justify-between pt-2">
              <div className="text-xs text-slate-400">
                Answered {Object.keys(answers).length} of {activeAssessment.questions.length} questions
              </div>
              <button
                type="button"
                disabled={submitting || Object.keys(answers).length < activeAssessment.questions.length}
                onClick={handleSubmitAssessment}
                className="rounded-lg bg-emerald-500 px-5 py-2.5 text-xs font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
              >
                {submitting ? 'Evaluating & Updating Mastery...' : 'Submit Assessment'}
              </button>
            </div>
          </div>
        </Panel>
      )}

      {/* Graded Result & Feedback View */}
      {gradedResult && (
        <Panel
          title={`Evaluation Report — ${gradedResult.assessment_title}`}
          subtitle={`Score: ${gradedResult.score_pct.toFixed(1)}% · Passing threshold: ${gradedResult.passing_score}%`}
          rightSlot={
            <button
              type="button"
              onClick={() => setGradedResult(null)}
              className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:text-white"
            >
              Close Report
            </button>
          }
        >
          <div className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-800 bg-navy-950/80 p-4">
              <div className="text-xs text-slate-400">Final Score</div>
              <div className="mt-1 font-mono text-2xl font-bold text-cyan-300">{gradedResult.score_pct.toFixed(1)}%</div>
              <div className="mt-1 text-xs text-slate-400">
                {gradedResult.points_earned} / {gradedResult.points_possible} points
              </div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-navy-950/80 p-4">
              <div className="text-xs text-slate-400">Outcome Status</div>
              <div className="mt-1.5 flex items-center gap-2 text-base font-bold">
                {gradedResult.passed ? (
                  <span className="text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="h-5 w-5" /> Passed Benchmark
                  </span>
                ) : (
                  <span className="text-amber-400 flex items-center gap-1.5">
                    <AlertCircle className="h-5 w-5" /> Needs Reinforcement
                  </span>
                )}
              </div>
            </div>
            {gradedResult.updated_prediction && (
              <div className="rounded-xl border border-slate-800 bg-navy-950/80 p-4">
                <div className="text-xs text-slate-400">Updated ML Forecast</div>
                <div className="mt-1 font-mono text-lg font-bold text-emerald-300">
                  {gradedResult.updated_prediction.predicted_final_score.toFixed(1)}% projected
                </div>
                <div className="mt-1 text-xs text-slate-400 capitalize">
                  Risk Tier: {gradedResult.updated_prediction.risk_level} ({gradedResult.updated_prediction.risk_score.toFixed(1)}%)
                </div>
              </div>
            )}
          </div>

          <div className="space-y-3">
            {gradedResult.items.map((item, idx) => (
              <div key={item.question_id} className="rounded-xl border border-slate-800 bg-navy-950/70 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-xs font-mono text-cyan-300 mb-1">
                      Item {idx + 1} · {item.concept_name}
                      {item.updated_concept_mastery !== undefined && (
                        <span className="ml-2 text-emerald-400">→ Mastery updated: {item.updated_concept_mastery}%</span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-slate-100">{item.prompt}</p>
                  </div>
                  {item.is_correct ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="h-5 w-5 text-rose-400 shrink-0" />
                  )}
                </div>
                <div className="mt-2.5 text-xs space-y-1">
                  <div className="text-slate-300">
                    Your Answer:{' '}
                    <span className={item.is_correct ? 'text-emerald-300 font-semibold' : 'text-rose-300 font-semibold'}>
                      {item.selected_index >= 0 ? item.options[item.selected_index] : 'No selection'}
                    </span>
                  </div>
                  {!item.is_correct && (
                    <div className="text-emerald-300">
                      Correct Answer: <span className="font-semibold">{item.options[item.correct_index]}</span>
                    </div>
                  )}
                  <div className="mt-1.5 rounded-lg bg-navy-900/90 border border-slate-800/80 p-2.5 text-slate-400">
                    <strong className="text-slate-200">Explanation:</strong> {item.explanation}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* Admin Psychometrics View */}
      {psychometrics && (
        <Panel
          title={`Psychometric Item Calibration — ${psychometrics.title}`}
          subtitle={`${psychometrics.submissions_count} cohort submissions · Mean ${psychometrics.mean_score}% · Pass Rate ${psychometrics.pass_rate}%`}
          rightSlot={
            <button
              type="button"
              onClick={() => setPsychometrics(null)}
              className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:text-white"
            >
              Close
            </button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <th className="py-2.5 pr-3">Question / Concept</th>
                  <th className="py-2.5 px-3">Difficulty Tag</th>
                  <th className="py-2.5 px-3">p-Value (Correct Rate)</th>
                  <th className="py-2.5 px-3">Discrimination (D)</th>
                  <th className="py-2.5 pl-3">Calibration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {psychometrics.items.map((it) => (
                  <tr key={it.question_id} className="hover:bg-navy-800/40">
                    <td className="py-3 pr-3 max-w-md">
                      <div className="font-medium text-slate-100 line-clamp-2">{it.prompt}</div>
                      <div className="font-mono text-[11px] text-cyan-400 mt-0.5">{it.concept_name}</div>
                    </td>
                    <td className="py-3 px-3 uppercase font-mono text-slate-300">{it.difficulty_tag}</td>
                    <td className="py-3 px-3 font-mono text-slate-200">{(it.difficulty_p_value * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3 font-mono font-semibold text-cyan-300">
                      {it.discrimination_index >= 0 ? `+${it.discrimination_index.toFixed(2)}` : it.discrimination_index.toFixed(2)}
                    </td>
                    <td className="py-3 pl-3">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold border ${
                          it.calibration_status === 'Strong Discriminator'
                            ? 'border-emerald-500/35 bg-emerald-500/15 text-emerald-300'
                            : it.calibration_status === 'Acceptable'
                            ? 'border-cyan-500/35 bg-cyan-500/15 text-cyan-300'
                            : 'border-amber-500/35 bg-amber-500/15 text-amber-300'
                        }`}
                      >
                        {it.calibration_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* Assessment Cards Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {assessments.map((a) => (
          <div key={a.id} className="enterprise-panel enterprise-panel-hover rounded-xl p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-semibold text-cyan-300 bg-cyan-500/15 border border-cyan-500/25 rounded px-2 py-0.5">
                  {a.course_code}
                </span>
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" /> {a.duration_minutes} min
                </span>
              </div>
              <h3 className="mt-3 text-base font-bold text-slate-100">{a.title}</h3>
              <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">{a.description}</p>
              <div className="mt-3 flex items-center gap-4 text-[11px] text-slate-400 font-mono">
                <span>{a.questions_count} Questions</span>
                <span>Pass: {a.passing_score}%</span>
                <span>{a.total_points} pts</span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2.5">
              {a.latest_submission ? (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Latest Attempt:</span>
                  <span
                    className={`font-mono font-semibold flex items-center gap-1 ${
                      a.latest_submission.passed ? 'text-emerald-400' : 'text-amber-400'
                    }`}
                  >
                    <Award className="h-3.5 w-3.5" />
                    {a.latest_submission.score_pct.toFixed(1)}%
                  </span>
                </div>
              ) : (
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Cohort Mean ({a.cohort_submissions_count} runs):</span>
                  <span className="font-mono text-slate-200">{a.cohort_mean_score.toFixed(1)}%</span>
                </div>
              )}

              <div className="flex items-center gap-2">
                {!isAdmin && (
                  <button
                    type="button"
                    onClick={() => startAssessment(a.id)}
                    className="flex-1 rounded-lg bg-cyan-500 px-3 py-2 text-xs font-semibold text-slate-950 hover:bg-cyan-400 flex items-center justify-center gap-1.5"
                  >
                    <ClipboardCheck className="h-3.5 w-3.5" />
                    {a.latest_submission ? 'Retake Assessment' : 'Start Assessment'}
                  </button>
                )}
                {a.latest_submission && (
                  <button
                    type="button"
                    onClick={() => viewPastSubmission(a.latest_submission!.submission_id)}
                    className="rounded-lg border border-slate-700 bg-navy-850 px-3 py-2 text-xs font-medium text-slate-200 hover:border-cyan-500/40"
                  >
                    Review
                  </button>
                )}
                {isAdmin && (
                  <button
                    type="button"
                    onClick={() => openPsychometrics(a.id)}
                    className="flex-1 rounded-lg border border-cyan-500/35 bg-cyan-500/15 px-3 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/25 flex items-center justify-center gap-1.5"
                  >
                    <Activity className="h-3.5 w-3.5" />
                    Inspect Item Psychometrics
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Admin Assessment Creation Modal */}
      {builderOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="enterprise-panel w-full max-w-xl rounded-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-slate-100">Author Concept-Mapped Assessment</h3>
              <button type="button" onClick={() => setBuilderOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            {builderError && (
              <div className="mt-3 rounded-lg border border-rose-500/40 bg-rose-500/10 p-2.5 text-xs text-rose-200">
                {builderError}
              </div>
            )}
            <form onSubmit={handleCreateAssessment} className="mt-4 space-y-3.5 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Course</label>
                  <select
                    value={newCourseId}
                    onChange={(e) => {
                      const cid = Number(e.target.value)
                      setNewCourseId(cid)
                      const m = concepts.filter((c) => c.course_id === cid)
                      if (m.length > 0) setQConceptId(m[0].id)
                    }}
                    className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                  >
                    {courses.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.code} — {c.title}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Target Concept</label>
                  <select
                    value={qConceptId}
                    onChange={(e) => setQConceptId(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                  >
                    {concepts
                      .filter((c) => c.course_id === newCourseId)
                      .map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.code} — {c.name}
                        </option>
                      ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Assessment Title</label>
                <input
                  type="text"
                  required
                  minLength={4}
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., DL-301 Backpropagation Diagnostic Check"
                  className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                />
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Description</label>
                <input
                  type="text"
                  required
                  minLength={8}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Targeted evaluation covering chain rule and gradient stability."
                  className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                />
              </div>
              <div className="border-t border-slate-800 pt-3">
                <div className="font-semibold text-cyan-300 mb-2">Initial Assessment Item</div>
                <textarea
                  required
                  minLength={10}
                  rows={2}
                  value={qPrompt}
                  onChange={(e) => setQPrompt(e.target.value)}
                  placeholder="Question prompt..."
                  className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                />
                <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {qOptions.map((opt, idx) => (
                    <input
                      key={idx}
                      type="text"
                      required
                      value={opt}
                      onChange={(e) => {
                        const copy = [...qOptions]
                        copy[idx] = e.target.value
                        setQOptions(copy)
                      }}
                      placeholder={`Option ${String.fromCharCode(65 + idx)}`}
                      className="rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                    />
                  ))}
                </div>
                <div className="mt-2 grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1">Correct Option</label>
                    <select
                      value={qCorrect}
                      onChange={(e) => setQCorrect(Number(e.target.value))}
                      className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                    >
                      <option value={0}>Option A</option>
                      <option value={1}>Option B</option>
                      <option value={2}>Option C</option>
                      <option value={3}>Option D</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-300 mb-1">Difficulty</label>
                    <select
                      value={qDifficulty}
                      onChange={(e) => setQDifficulty(e.target.value as 'easy' | 'medium' | 'hard')}
                      className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                </div>
                <div className="mt-2">
                  <label className="block text-slate-300 mb-1">Pedagogical Explanation</label>
                  <input
                    type="text"
                    required
                    minLength={8}
                    value={qExplanation}
                    onChange={(e) => setQExplanation(e.target.value)}
                    placeholder="Why this option is mathematically/conceptually correct..."
                    className="w-full rounded-lg border border-slate-700 bg-navy-950 px-3 py-2 text-slate-100"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setBuilderOpen(false)}
                  className="rounded-lg border border-slate-700 px-4 py-2 text-slate-300"
                >
                  Cancel
                </button>
                <button type="submit" className="rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-slate-950">
                  Publish Assessment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
