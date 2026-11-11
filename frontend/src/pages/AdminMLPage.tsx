import React, { useCallback, useEffect, useState } from 'react'
import { Cpu, RefreshCw } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'
import { KpiCard, LoadingSkeleton, PageHeader, Panel } from '../components/UiPrimitives'
import type { MLMetricsPayload } from '../types'

export const AdminMLPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MLMetricsPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [retraining, setRetraining] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  const loadMetrics = useCallback(async () => {
    try {
      const res = await api.get<MLMetricsPayload>('/ml/metrics')
      setMetrics(res)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMetrics()
  }, [loadMetrics])

  const handleRetrain = async () => {
    setRetraining(true)
    setToast(null)
    try {
      const res = await api.post<{ status: string; metrics: MLMetricsPayload }>('/ml/retrain')
      setMetrics(res.metrics)
      setToast(
        `Retrained pipelines on ${res.metrics.cohort_size} learner records. Active classifier: ${res.metrics.risk_model.selected_classifier}.`
      )
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Retraining failed.')
    } finally {
      setRetraining(false)
    }
  }

  if (loading) return <LoadingSkeleton />
  if (!metrics) return <div className="enterprise-panel rounded-xl p-6 text-rose-300">ML telemetry unavailable.</div>

  const { risk_model, clustering_model } = metrics
  const cm = risk_model.confusion_matrix.matrix

  return (
    <div className="space-y-6">
      {toast && (
        <div className="flex items-center justify-between rounded-xl border border-cyan-500/35 bg-cyan-500/10 px-4 py-3 text-xs text-cyan-200">
          <span>{toast}</span>
          <button type="button" onClick={() => setToast(null)} className="font-semibold text-cyan-300">
            Dismiss
          </button>
        </div>
      )}

      <PageHeader
        title="ML Pipeline & Evaluation Console"
        subtitle={`Measured ${risk_model.cv_folds}-fold cross-validation & unsupervised clustering metrics · Trained ${new Date(
          metrics.trained_at
        ).toLocaleString()}`}
        actions={
          <button
            type="button"
            disabled={retraining}
            onClick={handleRetrain}
            className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${retraining ? 'animate-spin' : ''}`} />
            {retraining ? 'Retraining Pipelines...' : 'Retrain Models Live'}
          </button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Selected Risk Classifier"
          value={`${(risk_model.classifier_metrics.accuracy * 100).toFixed(1)}%`}
          subtext={`${risk_model.selected_classifier} · F1 ${risk_model.classifier_metrics.f1_score.toFixed(3)}`}
          icon={Cpu}
          accent="cyan"
        />
        <KpiCard
          label="Classifier ROC-AUC"
          value={risk_model.classifier_metrics.roc_auc.toFixed(3)}
          subtext={`${risk_model.cv_folds}-Fold Stratified CV (n=${risk_model.sample_size})`}
          icon={Cpu}
          accent="emerald"
        />
        <KpiCard
          label="Score Regressor RMSE"
          value={risk_model.regressor_metrics.rmse.toFixed(2)}
          subtext={`${risk_model.selected_regressor} · R2 ${risk_model.regressor_metrics.r2_score.toFixed(3)}`}
          icon={Cpu}
          accent="amber"
        />
        <KpiCard
          label="K-Means Silhouette"
          value={clustering_model.silhouette_score.toFixed(3)}
          subtext={`Calinski-Harabasz ${clustering_model.calinski_harabasz_score} (k=${clustering_model.n_clusters})`}
          icon={Cpu}
          accent="cyan"
        />
      </div>

      {/* Supervised Classifier Benchmark + Confusion Matrix */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Panel
          title="Supervised Classifier Cross-Validation Benchmark"
          subtitle="Measured out-of-fold classification performance across candidate algorithms"
          className="lg:col-span-2"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <th className="py-2.5 pr-3">Model Pipeline</th>
                  <th className="py-2.5 px-3">Accuracy</th>
                  <th className="py-2.5 px-3">Precision</th>
                  <th className="py-2.5 px-3">Recall</th>
                  <th className="py-2.5 px-3">F1-Score</th>
                  <th className="py-2.5 pl-3 text-right">ROC-AUC</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {risk_model.classifier_comparison.map((row) => {
                  const selected = row.model === risk_model.selected_classifier
                  return (
                    <tr key={row.model} className={selected ? 'bg-cyan-500/10' : ''}>
                      <td className="py-3 pr-3 font-semibold text-slate-100">
                        {row.model}
                        {selected && (
                          <span className="ml-2 rounded bg-cyan-500/20 px-1.5 py-0.5 text-[10px] text-cyan-300">
                            ACTIVE
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-200">{(row.accuracy * 100).toFixed(1)}%</td>
                      <td className="py-3 px-3 font-mono text-slate-200">{row.precision.toFixed(3)}</td>
                      <td className="py-3 px-3 font-mono text-slate-200">{row.recall.toFixed(3)}</td>
                      <td className="py-3 px-3 font-mono font-semibold text-emerald-300">{row.f1_score.toFixed(3)}</td>
                      <td className="py-3 pl-3 text-right font-mono font-semibold text-cyan-300">{row.roc_auc.toFixed(3)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-5 pt-4 border-t border-slate-800">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Score Prediction Regressors (K-Fold CV)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {risk_model.regressor_comparison.map((r) => (
                <div
                  key={r.model}
                  className={`rounded-xl border p-3.5 text-xs ${
                    r.model === risk_model.selected_regressor
                      ? 'border-emerald-500/40 bg-emerald-500/10'
                      : 'border-slate-800 bg-navy-950/75'
                  }`}
                >
                  <div className="font-semibold text-slate-100">{r.model}</div>
                  <div className="mt-2 flex justify-between font-mono text-slate-300">
                    <span>MAE: {r.mae}</span>
                    <span>RMSE: {r.rmse}</span>
                    <span className="text-emerald-300">R2: {r.r2_score}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        <Panel
          title="Out-of-Fold Confusion Matrix"
          subtitle={`At-risk prevalence: ${risk_model.positive_risk_count} / ${risk_model.sample_size} students`}
        >
          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
              <div className="text-[10px] uppercase text-emerald-300 font-semibold">True Negative</div>
              <div className="font-mono text-2xl font-bold text-slate-100 mt-1">{cm[0][0]}</div>
              <div className="text-[11px] text-slate-400 mt-1">Predicted On Track</div>
            </div>
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <div className="text-[10px] uppercase text-amber-300 font-semibold">False Positive</div>
              <div className="font-mono text-2xl font-bold text-slate-100 mt-1">{cm[0][1]}</div>
              <div className="text-[11px] text-slate-400 mt-1">Flagged Early</div>
            </div>
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4">
              <div className="text-[10px] uppercase text-rose-300 font-semibold">False Negative</div>
              <div className="font-mono text-2xl font-bold text-slate-100 mt-1">{cm[1][0]}</div>
              <div className="text-[11px] text-slate-400 mt-1">Missed At-Risk</div>
            </div>
            <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-4">
              <div className="text-[10px] uppercase text-cyan-300 font-semibold">True Positive</div>
              <div className="font-mono text-2xl font-bold text-slate-100 mt-1">{cm[1][1]}</div>
              <div className="text-[11px] text-slate-400 mt-1">Correctly Flagged</div>
            </div>
          </div>
        </Panel>
      </div>

      {/* Feature Importances & Cluster Profiles */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel title="Global Feature Importances" subtitle="Random Forest Gini importance across engineered behavioral features">
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={risk_model.feature_importances.slice(0, 9)}
                layout="vertical"
                margin={{ top: 4, right: 20, left: 10, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" horizontal={false} />
                <XAxis type="number" stroke="#64748B" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="label"
                  width={165}
                  stroke="#94A3B8"
                  fontSize={11}
                  tickFormatter={(v: string) => (v.length > 23 ? `${v.slice(0, 22)}...` : v)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1120',
                    borderColor: 'rgba(34,211,238,0.3)',
                    borderRadius: '0.6rem',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="importance" fill="#22D3EE" radius={[0, 5, 5, 0]} name="Importance Weight" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title="Unsupervised Learner Cluster Centroids"
          subtitle={`PCA 2D explained variance: ${(
            (clustering_model.pca_explained_variance_ratio[0] + clustering_model.pca_explained_variance_ratio[1]) *
            100
          ).toFixed(1)}%`}
        >
          <div className="space-y-3">
            {clustering_model.clusters.map((cl) => (
              <div key={cl.cluster_id} className="rounded-xl border border-slate-800 bg-navy-950/75 p-3.5">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-cyan-300">{cl.label}</span>
                  <span className="font-mono text-xs text-slate-300">{cl.student_count} students</span>
                </div>
                <p className="mt-1 text-xs text-slate-400">{cl.description}</p>
                <div className="mt-2.5 grid grid-cols-3 gap-2 font-mono text-[11px] text-slate-300">
                  <div>Mastery: {cl.centroid.avg_concept_mastery}%</div>
                  <div>Hours/wk: {cl.centroid.avg_study_hours}h</div>
                  <div>Attend: {cl.centroid.attendance_rate}%</div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}
