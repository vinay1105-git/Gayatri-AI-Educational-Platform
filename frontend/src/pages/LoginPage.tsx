import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Lock, Mail, Shield, Sparkles, User as UserIcon } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../api/client'
import { BrandLogo } from '../components/BrandLogo'

const COHORT_OPTIONS = [
  'Fall 2026 - AI Engineering',
  'Spring 2026 - Applied ML',
  'Summer 2026 - Data Systems',
  'Fall 2026 - MLOps Track',
]

const TRACK_OPTIONS = [
  'Applied Artificial Intelligence',
  'Machine Learning Systems',
  'Data Engineering & Analytics',
  'Production MLOps',
]

export const LoginPage: React.FC = () => {
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [cohort, setCohort] = useState(COHORT_OPTIONS[0])
  const [track, setTrack] = useState(TRACK_OPTIONS[0])
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (mode === 'login') {
        const u = await login(email, password)
        navigate(u.role === 'admin' ? '/admin' : '/dashboard')
      } else {
        const u = await register({
          full_name: fullName,
          email,
          password,
          cohort,
          program_track: track,
        })
        navigate(u.role === 'admin' ? '/admin' : '/dashboard')
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to authenticate. Please verify your credentials.')
    } finally {
      setSubmitting(false)
    }
  }

  const quickFillDemo = (demoEmail: string, demoPassword: string) => {
    setMode('login')
    setEmail(demoEmail)
    setPassword(demoPassword)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col lg:flex-row">
      {/* Left Brand & Architecture Overview */}
      <div className="lg:w-[48%] border-b lg:border-b-0 lg:border-r border-slate-800/80 bg-gradient-to-br from-navy-900 via-navy-950 to-navy-900 p-8 sm:p-12 flex flex-col justify-between">
        <div>
          <BrandLogo size={40} showSubtitle />

          <div className="mt-12 max-w-lg">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-300 mb-5">
              <Sparkles className="h-3.5 w-3.5" />
              Predictive Learning & Academic Intelligence
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100 leading-tight">
              Precision Analytics for Modern AI & Engineering Cohorts
            </h1>
            <p className="mt-4 text-sm sm:text-base text-slate-400 leading-relaxed">
              Gayatri AI unifies longitudinal telemetry, cross-validated risk modeling, Bayesian concept mastery tracing,
              and curriculum-grounded academic tutoring inside a single enterprise platform.
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-lg">
            <div className="rounded-xl border border-slate-800 bg-navy-900/70 p-4">
              <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Predictive Modeling</div>
              <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                Scikit-learn ensemble risk stratification with transparent local feature attribution drivers.
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-navy-900/70 p-4">
              <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Knowledge Tracing</div>
              <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                Prerequisite-aware concept mastery estimation paired with TF-IDF hybrid resource recommendations.
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-navy-900/70 p-4">
              <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Psychometric Testing</div>
              <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                Automated evaluation engine computing real item difficulty and upper-lower discrimination indices.
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-navy-900/70 p-4">
              <div className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Executive Exports</div>
              <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                On-demand formatted PDF intelligence transcripts and cohort telemetry CSV datasets.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-slate-800/80 text-xs text-slate-500 flex items-center justify-between">
          <span>Gayatri AI Enterprise Platform</span>
          <span className="font-mono">v1.0.0 · RBAC & Audit Enabled</span>
        </div>
      </div>

      {/* Right Authentication Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md">
          <div className="enterprise-panel rounded-2xl p-6 sm:p-8">
            <div className="flex rounded-lg bg-navy-950 p-1 border border-slate-800 mb-6">
              <button
                type="button"
                onClick={() => {
                  setMode('login')
                  setError(null)
                }}
                className={`flex-1 rounded-md py-2 text-xs font-semibold transition-colors ${
                  mode === 'login' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('register')
                  setError(null)
                }}
                className={`flex-1 rounded-md py-2 text-xs font-semibold transition-colors ${
                  mode === 'register' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                New Student Enrollment
              </button>
            </div>

            <h2 className="text-xl font-bold text-slate-100">
              {mode === 'login' ? 'Access Your Workspace' : 'Create Student Account'}
            </h2>
            <p className="mt-1 text-xs text-slate-400">
              {mode === 'login'
                ? 'Authenticate with institutional credentials to view personalized analytics.'
                : 'Enroll in the AI & Machine Learning curriculum with automated telemetry.'}
            </p>

            {error && (
              <div className="mt-4 rounded-lg border border-rose-500/40 bg-rose-500/10 px-3.5 py-2.5 text-xs text-rose-200">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              {mode === 'register' && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Full Name</label>
                  <div className="relative">
                    <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g., Priya Nair"
                      className="w-full rounded-lg border border-slate-700/80 bg-navy-950 pl-9 pr-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Institutional Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@gayatri-ai.edu"
                    className="w-full rounded-lg border border-slate-700/80 bg-navy-950 pl-9 pr-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    type="password"
                    required
                    minLength={mode === 'register' ? 8 : 6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={mode === 'register' ? 'Minimum 8 characters' : 'Enter password'}
                    className="w-full rounded-lg border border-slate-700/80 bg-navy-950 pl-9 pr-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              </div>

              {mode === 'register' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Cohort</label>
                    <select
                      value={cohort}
                      onChange={(e) => setCohort(e.target.value)}
                      className="w-full rounded-lg border border-slate-700/80 bg-navy-950 px-3 py-2 text-xs text-slate-100 focus:border-cyan-500 focus:outline-none"
                    >
                      {COHORT_OPTIONS.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">Specialization Track</label>
                    <select
                      value={track}
                      onChange={(e) => setTrack(e.target.value)}
                      className="w-full rounded-lg border border-slate-700/80 bg-navy-950 px-3 py-2 text-xs text-slate-100 focus:border-cyan-500 focus:outline-none"
                    >
                      {TRACK_OPTIONS.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-60 transition-colors"
              >
                <span>{submitting ? 'Authenticating...' : mode === 'login' ? 'Sign In to Platform' : 'Complete Enrollment'}</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            {/* Demo Evaluation Quick-Fill Credentials */}
            <div className="mt-6 pt-5 border-t border-slate-800/90">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-3">
                <Shield className="h-3.5 w-3.5 text-cyan-400" />
                Seeded Evaluation Accounts (Quick Fill)
              </div>
              <div className="grid grid-cols-1 gap-2">
                <button
                  type="button"
                  onClick={() => quickFillDemo('ananya.sharma@gayatri-ai.edu', 'Student@2026')}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-navy-950/90 px-3 py-2 text-left hover:border-cyan-500/40 transition-colors"
                >
                  <div>
                    <div className="text-xs font-semibold text-slate-200">Ananya Sharma · Student</div>
                    <div className="font-mono text-[11px] text-slate-500">ananya.sharma@gayatri-ai.edu</div>
                  </div>
                  <span className="rounded bg-cyan-500/15 px-2 py-0.5 text-[10px] font-medium text-cyan-300">Fill</span>
                </button>
                <button
                  type="button"
                  onClick={() => quickFillDemo('rohan.verma@gayatri-ai.edu', 'Student@2026')}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-navy-950/90 px-3 py-2 text-left hover:border-amber-500/40 transition-colors"
                >
                  <div>
                    <div className="text-xs font-semibold text-slate-200">Rohan Verma · At-Risk Learner</div>
                    <div className="font-mono text-[11px] text-slate-500">rohan.verma@gayatri-ai.edu</div>
                  </div>
                  <span className="rounded bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium text-amber-300">Fill</span>
                </button>
                <button
                  type="button"
                  onClick={() => quickFillDemo('admin@gayatri-ai.edu', 'Admin@Gayatri2026')}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-navy-950/90 px-3 py-2 text-left hover:border-emerald-500/40 transition-colors"
                >
                  <div>
                    <div className="text-xs font-semibold text-slate-200">Dr. Kavita Rao · Administrator</div>
                    <div className="font-mono text-[11px] text-slate-500">admin@gayatri-ai.edu</div>
                  </div>
                  <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium text-emerald-300">Fill</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
