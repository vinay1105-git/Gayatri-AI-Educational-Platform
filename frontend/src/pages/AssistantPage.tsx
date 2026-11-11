import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, MessageSquareText, Send, Sparkles, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { PageHeader } from '../components/UiPrimitives'
import type { AssistantChatMessage } from '../types'

const FormattedContent: React.FC<{ text: string }> = ({ text }) => {
  const lines = text.split('\n')
  return (
    <div className="space-y-1.5 text-sm leading-relaxed text-slate-200">
      {lines.map((line, i) => {
        const trimmed = line.trim()
        if (!trimmed) return <div key={i} className="h-1" />
        if (trimmed.startsWith('### ')) {
          return (
            <h4 key={i} className="text-base font-bold text-cyan-300 pt-1">
              {trimmed.slice(4)}
            </h4>
          )
        }
        const renderInline = (segment: string) => {
          const parts = segment.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g)
          return parts.map((p, idx) => {
            if (p.startsWith('**') && p.endsWith('**')) {
              return (
                <strong key={idx} className="font-semibold text-white">
                  {p.slice(2, -2)}
                </strong>
              )
            }
            if (p.startsWith('`') && p.endsWith('`')) {
              return (
                <code key={idx} className="rounded bg-navy-900 px-1.5 py-0.5 font-mono text-xs text-cyan-300 border border-slate-700/70">
                  {p.slice(1, -1)}
                </code>
              )
            }
            if (p.startsWith('*') && p.endsWith('*') && p.length > 2) {
              return (
                <em key={idx} className="italic text-slate-300">
                  {p.slice(1, -1)}
                </em>
              )
            }
            return <React.Fragment key={idx}>{p}</React.Fragment>
          })
        }
        if (trimmed.startsWith('- ') || /^\d+\.\s/.test(trimmed)) {
          return (
            <div key={i} className="pl-3 flex items-start gap-2">
              <span className="text-cyan-400 font-mono text-xs mt-1">•</span>
              <span className="flex-1">{renderInline(trimmed.replace(/^- /, '').replace(/^\d+\.\s/, ''))}</span>
            </div>
          )
        }
        return <p key={i}>{renderInline(trimmed)}</p>
      })}
    </div>
  )
}

export const AssistantPage: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const isAdmin = user?.role === 'admin'

  const [messages, setMessages] = useState<AssistantChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const quickPrompts = isAdmin
    ? [
        'Which students need urgent academic intervention?',
        'Summarize lowest cohort concept mastery and model telemetry',
        'Explain Population Stability Index (PSI) and concept drift monitoring',
      ]
    : [
        'Diagnose my performance, risk score, and concept gaps',
        'Build me a personalized study plan for this week',
        'Explain Backpropagation and how residual connections fix vanishing gradients',
        'How does Scaled Dot-Product Self-Attention work in Transformers?',
      ]

  const loadHistory = useCallback(async () => {
    try {
      const res = await api.get<{ messages: AssistantChatMessage[] }>('/assistant/history?session_id=default')
      setMessages(res.messages)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendQuery = async (queryText: string) => {
    const trimmed = queryText.trim()
    if (!trimmed || sending) return
    setSending(true)
    setInput('')

    const optimisticUser: AssistantChatMessage = {
      id: Date.now(),
      role: 'user',
      content: trimmed,
      citations: [],
      suggested_actions: [],
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimisticUser])

    try {
      const res = await api.post<{ message: AssistantChatMessage }>('/assistant/query', {
        query: trimmed,
        session_id: 'default',
      })
      setMessages((prev) => [...prev, res.message])
    } catch (err) {
      const errMsg: AssistantChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: err instanceof Error ? err.message : 'Unable to process query.',
        citations: [],
        suggested_actions: [],
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setSending(false)
    }
  }

  const clearHistory = async () => {
    await api.del('/assistant/history?session_id=default')
    setMessages([])
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Academic Intelligence Assistant"
        subtitle="Hybrid TF-IDF curriculum retrieval grounded in your live mastery, trajectory, and institutional telemetry"
        actions={
          messages.length > 0 ? (
            <button
              type="button"
              onClick={clearHistory}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-navy-850 px-3 py-2 text-xs font-medium text-slate-300 hover:border-rose-500/40 hover:text-rose-200"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear Session
            </button>
          ) : undefined
        }
      />

      <div className="enterprise-panel rounded-2xl flex flex-col h-[calc(100vh-230px)] min-h-[500px] overflow-hidden">
        {/* Conversation Feed */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {!loading && messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto px-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-500/30 bg-cyan-500/15 text-cyan-300 mb-4">
                <MessageSquareText className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Gayatri Academic Intelligence Engine</h3>
              <p className="mt-2 text-xs sm:text-sm text-slate-400 leading-relaxed">
                Ask technical questions across AI, Deep Learning, Transformers, and MLOps, or request a live diagnostic
                and adaptive study plan grounded in your telemetry.
              </p>
              <div className="mt-6 grid grid-cols-1 gap-2.5 w-full">
                {quickPrompts.map((qp) => (
                  <button
                    key={qp}
                    type="button"
                    onClick={() => sendQuery(qp)}
                    className="rounded-xl border border-slate-800 bg-navy-950/80 px-4 py-3 text-left text-xs font-medium text-slate-200 hover:border-cyan-500/40 hover:bg-navy-850 transition-colors flex items-center justify-between gap-3"
                  >
                    <span>{qp}</span>
                    <Sparkles className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-3xl rounded-2xl px-4 py-3.5 ${
                  m.role === 'user'
                    ? 'bg-cyan-500/15 border border-cyan-500/30 text-slate-100'
                    : 'bg-navy-950/90 border border-slate-800 text-slate-200 w-full'
                }`}
              >
                {m.role === 'user' ? (
                  <p className="text-sm font-medium">{m.content}</p>
                ) : (
                  <div className="space-y-3">
                    <FormattedContent text={m.content} />

                    {m.citations && m.citations.length > 0 && (
                      <div className="pt-2.5 border-t border-slate-800/80">
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1">
                          <BookOpen className="h-3 w-3 text-cyan-400" />
                          Curriculum Citations
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {m.citations.map((c, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center gap-1.5 rounded-md border border-slate-700/80 bg-navy-900 px-2 py-1 text-[11px] text-slate-300"
                            >
                              <span className="font-mono text-cyan-400">{c.course_code}</span>
                              <span>{c.title}</span>
                              <span className="font-mono text-[10px] text-emerald-400">
                                {(c.relevance * 100).toFixed(0)}%
                              </span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {m.suggested_actions && m.suggested_actions.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {m.suggested_actions.map((act, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => navigate(act.route)}
                            className="inline-flex items-center gap-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-300 hover:bg-emerald-500/20"
                          >
                            {act.label}
                            <ArrowRight className="h-3 w-3" />
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="rounded-xl border border-slate-800 bg-navy-950/90 px-4 py-3 text-xs text-cyan-300 animate-pulse">
                Retrieving curriculum context & student telemetry...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Prompt Bar */}
        <div className="border-t border-slate-800/80 bg-navy-900/90 p-3.5 sm:p-4">
          {messages.length > 0 && (
            <div className="mb-2.5 flex gap-2 overflow-x-auto pb-1">
              {quickPrompts.slice(0, 3).map((qp) => (
                <button
                  key={qp}
                  type="button"
                  onClick={() => sendQuery(qp)}
                  className="shrink-0 rounded-full border border-slate-700/80 bg-navy-950 px-3 py-1 text-[11px] text-slate-300 hover:border-cyan-500/40 hover:text-cyan-200"
                >
                  {qp}
                </button>
              ))}
            </div>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              sendQuery(input)
            }}
            className="flex items-center gap-2.5"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a concept, request your performance diagnostic, or build a weekly study plan..."
              className="flex-1 rounded-xl border border-slate-700/80 bg-navy-950 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!input.trim() || sending}
              className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2.5 text-xs font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
