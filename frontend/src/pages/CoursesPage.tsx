import React, { useCallback, useEffect, useState } from 'react'
import { BookOpen, CheckCircle2, Clock, Compass, GitBranch, Layers, Sparkles, X } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { LoadingSkeleton, PageHeader, Panel } from '../components/UiPrimitives'
import type { CourseItem, RecommendationItem } from '../types'

interface CourseDetail {
  id: number
  code: string
  title: string
  category: string
  difficulty: string
  instructor_name: string
  description: string
  concepts: Array<{
    id: number
    code: string
    name: string
    description: string
    difficulty_weight: number
    prerequisite_name: string | null
    key_notes: string
    mastery_score: number | null
  }>
  resources: Array<{
    id: number
    title: string
    resource_type: string
    difficulty: string
    estimated_minutes: number
    summary: string
    content_body: string
    concept_name: string
    tags: string[]
    interaction_status: string
  }>
}

export const CoursesPage: React.FC = () => {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'

  const [courses, setCourses] = useState<CourseItem[]>([])
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([])
  const [selectedCourse, setSelectedCourse] = useState<CourseDetail | null>(null)
  const [activeResource, setActiveResource] = useState<{
    id: number
    title: string
    subtitle: string
    body: string
    status: string
  } | null>(null)

  const [tab, setTab] = useState<'recommended' | 'catalog'>(isStudent ? 'recommended' : 'catalog')
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState<string | null>(null)

  const loadAll = useCallback(async () => {
    try {
      const cRes = await api.get<{ courses: CourseItem[] }>('/courses')
      setCourses(cRes.courses)
      if (isStudent) {
        const rRes = await api.get<{ recommendations: RecommendationItem[] }>('/courses/recommendations?limit=12')
        setRecommendations(rRes.recommendations)
      }
    } finally {
      setLoading(false)
    }
  }, [isStudent])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const openCourseDetail = async (courseId: number) => {
    const detail = await api.get<CourseDetail>(`/courses/${courseId}`)
    setSelectedCourse(detail)
  }

  const updateInteraction = async (resourceId: number, status: 'viewed' | 'bookmarked' | 'completed') => {
    await api.post(`/courses/resources/${resourceId}/interact`, { status, rating: status === 'completed' ? 5 : undefined })
    setToast(
      status === 'completed'
        ? 'Module completed. Concept mastery and ML forecasts refreshed.'
        : `Module marked as ${status}.`
    )
    await loadAll()
    if (selectedCourse) {
      await openCourseDetail(selectedCourse.id)
    }
    if (activeResource && activeResource.id === resourceId) {
      setActiveResource({ ...activeResource, status })
    }
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
        title={isStudent ? 'Courses & Adaptive Learning Path' : 'Institutional Curriculum Catalog'}
        subtitle={
          isStudent
            ? 'Personalized TF-IDF & mastery-gap recommendations paired with prerequisite concept graphs'
            : 'Explore all AI & Machine Learning courses, prerequisite concepts, and instructional resources'
        }
        actions={
          isStudent ? (
            <div className="flex rounded-lg border border-slate-800 bg-navy-900 p-1">
              <button
                type="button"
                onClick={() => setTab('recommended')}
                className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                  tab === 'recommended' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Recommended For You ({recommendations.length})
              </button>
              <button
                type="button"
                onClick={() => setTab('catalog')}
                className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                  tab === 'catalog' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                All Courses ({courses.length})
              </button>
            </div>
          ) : undefined
        }
      />

      {tab === 'recommended' && isStudent && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {recommendations.map((rec) => (
            <div
              key={rec.resource_id}
              className="enterprise-panel enterprise-panel-hover rounded-xl p-5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-semibold text-cyan-300 bg-cyan-500/15 border border-cyan-500/25 rounded px-2 py-0.5">
                    {rec.course_code}
                  </span>
                  <span className="font-mono text-xs font-semibold text-emerald-400">{rec.match_score}% match</span>
                </div>
                <h3 className="mt-3 text-base font-semibold text-slate-100 leading-snug">{rec.title}</h3>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                  <span className="rounded bg-navy-800 px-2 py-0.5 text-slate-300">{rec.resource_type}</span>
                  <span className="rounded bg-navy-800 px-2 py-0.5 text-amber-300">{rec.difficulty}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" /> {rec.estimated_minutes} min
                  </span>
                </div>
                <p className="mt-3 text-xs text-slate-400 leading-relaxed">{rec.rationale}</p>
                <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-2.5">
                  <span>Concept: {rec.concept_name}</span>
                  <span className="font-mono text-slate-200">{rec.current_concept_mastery}%</span>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setActiveResource({
                      id: rec.resource_id,
                      title: rec.title,
                      subtitle: `${rec.course_code} · ${rec.concept_name} · ${rec.resource_type}`,
                      body: rec.content_body,
                      status: rec.interaction_status,
                    })
                  }
                  className="flex-1 rounded-lg border border-cyan-500/35 bg-cyan-500/15 px-3 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/25"
                >
                  Open Study Module
                </button>
                {rec.interaction_status === 'completed' ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-2 text-xs font-semibold text-emerald-400">
                    <CheckCircle2 className="h-4 w-4" /> Completed
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => updateInteraction(rec.resource_id, 'completed')}
                    className="rounded-lg border border-emerald-500/35 bg-emerald-500/15 px-3 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/25"
                  >
                    Complete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {(tab === 'catalog' || !isStudent) && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {courses.map((course) => (
            <div
              key={course.id}
              className="enterprise-panel enterprise-panel-hover rounded-xl p-5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-semibold text-cyan-300 bg-cyan-500/15 border border-cyan-500/25 rounded px-2 py-0.5">
                    {course.code}
                  </span>
                  <span className="text-[11px] font-medium text-amber-300 bg-amber-500/10 border border-amber-500/25 rounded-full px-2.5 py-0.5">
                    {course.difficulty}
                  </span>
                </div>
                <h3 className="mt-3 text-base font-bold text-slate-100">{course.title}</h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">{course.description}</p>
                <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <Layers className="h-3.5 w-3.5 text-cyan-400" /> {course.concepts_count} Concepts
                  </span>
                  <span className="flex items-center gap-1">
                    <BookOpen className="h-3.5 w-3.5 text-emerald-400" /> {course.resources_count} Modules
                  </span>
                  <span>{course.instructor_name}</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80">
                {course.student_progress !== null ? (
                  <div className="mb-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Progress</span>
                      <span className="font-mono text-slate-200">
                        {course.student_progress}% · Grade {course.student_grade}%
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400"
                        style={{ width: `${course.student_progress}%` }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="mb-3 flex justify-between text-xs text-slate-400">
                    <span>Cohort Enrolled: {course.enrolled_count}</span>
                    <span className="font-mono text-slate-200">Mean Grade: {course.cohort_avg_grade}%</span>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => openCourseDetail(course.id)}
                  className="w-full rounded-lg border border-slate-700 bg-navy-850 px-3 py-2 text-xs font-semibold text-slate-200 hover:border-cyan-500/40 hover:text-cyan-200 transition-colors flex items-center justify-center gap-1.5"
                >
                  <Compass className="h-3.5 w-3.5" />
                  Inspect Concepts & Resources
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Course Concept & Module Drawer */}
      {selectedCourse && (
        <Panel
          title={`${selectedCourse.code}: ${selectedCourse.title}`}
          subtitle={`${selectedCourse.instructor_name} · ${selectedCourse.category}`}
          rightSlot={
            <button
              type="button"
              onClick={() => setSelectedCourse(null)}
              className="rounded-lg border border-slate-700 p-1.5 text-slate-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          }
        >
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-cyan-400 mb-3">
                Prerequisite Concept Graph & Mastery
              </h3>
              <div className="space-y-3">
                {selectedCourse.concepts.map((c) => (
                  <div key={c.id} className="rounded-xl border border-slate-800 bg-navy-950/75 p-3.5">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] text-cyan-300">{c.code}</span>
                        <span className="text-sm font-semibold text-slate-100">{c.name}</span>
                      </div>
                      {c.mastery_score !== null && (
                        <span className="font-mono text-xs font-semibold text-emerald-400">{c.mastery_score}%</span>
                      )}
                    </div>
                    {c.prerequisite_name && (
                      <div className="mt-1 flex items-center gap-1.5 text-[11px] text-amber-300">
                        <GitBranch className="h-3 w-3" /> Prerequisite: {c.prerequisite_name}
                      </div>
                    )}
                    <p className="mt-1.5 text-xs text-slate-400">{c.description}</p>
                    <pre className="mt-2 whitespace-pre-wrap font-sans text-[11px] text-slate-300 bg-navy-900/90 rounded-lg p-2.5 border border-slate-800/80">
                      {c.key_notes}
                    </pre>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-3">
                Instructional Study Modules
              </h3>
              <div className="space-y-3">
                {selectedCourse.resources.map((r) => (
                  <div key={r.id} className="rounded-xl border border-slate-800 bg-navy-950/75 p-3.5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[11px] font-medium text-cyan-300">{r.resource_type}</span>
                        <h4 className="text-sm font-semibold text-slate-100 mt-0.5">{r.title}</h4>
                      </div>
                      <span className="font-mono text-[11px] text-slate-400">{r.estimated_minutes}m</span>
                    </div>
                    <p className="mt-1.5 text-xs text-slate-400">{r.summary}</p>
                    <div className="mt-3 flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() =>
                          setActiveResource({
                            id: r.id,
                            title: r.title,
                            subtitle: `${selectedCourse.code} · ${r.concept_name}`,
                            body: r.content_body,
                            status: r.interaction_status,
                          })
                        }
                        className="rounded-md border border-cyan-500/35 bg-cyan-500/15 px-3 py-1.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/25"
                      >
                        Read Module
                      </button>
                      {isStudent && r.interaction_status !== 'completed' && (
                        <button
                          type="button"
                          onClick={() => updateInteraction(r.id, 'completed')}
                          className="rounded-md border border-emerald-500/35 bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/25"
                        >
                          Mark Completed
                        </button>
                      )}
                      {isStudent && r.interaction_status === 'completed' && (
                        <span className="inline-flex items-center gap-1 text-xs text-emerald-400 font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Completed
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Panel>
      )}

      {/* Study Reader Modal */}
      {activeResource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="enterprise-panel w-full max-w-2xl rounded-2xl p-6 max-h-[88vh] overflow-y-auto">
            <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400">
                  <Sparkles className="h-3.5 w-3.5" />
                  {activeResource.subtitle}
                </div>
                <h3 className="mt-1 text-lg font-bold text-slate-100">{activeResource.title}</h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveResource(null)}
                className="rounded-lg border border-slate-700 p-1.5 text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <pre className="mt-4 whitespace-pre-wrap font-sans text-sm text-slate-200 leading-relaxed bg-navy-950/90 rounded-xl p-4 border border-slate-800">
              {activeResource.body}
            </pre>
            <div className="mt-5 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setActiveResource(null)}
                className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-navy-800"
              >
                Close
              </button>
              {isStudent && activeResource.status !== 'completed' && (
                <button
                  type="button"
                  onClick={() => updateInteraction(activeResource.id, 'completed')}
                  className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-emerald-400"
                >
                  Mark Module Completed
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
