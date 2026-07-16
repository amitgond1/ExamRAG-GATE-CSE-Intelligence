import { FlaskConical, Play } from 'lucide-react'
import { useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { runABTest } from '../api'

const defaultQuestions = [
  {
    question: 'What are the four necessary conditions for deadlock?',
    ground_truth: 'Mutual exclusion, hold and wait, no preemption, and circular wait.',
    expected_topic: 'Deadlock',
  },
  {
    question: 'When is a relation in BCNF?',
    ground_truth: 'A relation is in BCNF when every non-trivial functional dependency has a superkey as its determinant.',
    expected_topic: 'Normalization',
  },
  {
    question: 'What is the time complexity of Dijkstra using a binary heap?',
    ground_truth: 'O((V + E) log V), commonly written O(E log V) for a connected graph.',
    expected_topic: 'Shortest paths',
  },
]

const strategyNames = {
  dense: 'A · Dense',
  hybrid: 'B · Hybrid',
  hybrid_rerank: 'C · Hybrid + rerank',
}

export default function ABTesting() {
  const [items, setItems] = useState(defaultQuestions)
  const [results, setResults] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  function update(index, key, value) {
    setItems((old) => old.map((item, itemIndex) => (
      itemIndex === index ? { ...item, [key]: value } : item
    )))
  }

  async function run() {
    setBusy(true)
    setError('')
    try {
      const validItems = items.filter((item) => item.question && item.ground_truth)
      const response = await runABTest(validItems)
      setResults(response.results)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Experiment failed')
    } finally {
      setBusy(false)
    }
  }

  const chart = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
    .map((metric) => ({
      metric: metric.replace('_', ' '),
      ...Object.fromEntries(results.map((result) => [
        result.strategy,
        (result.metrics[metric] ?? 0) * 100,
      ])),
    }))

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-bold uppercase tracking-widest text-brand-600">Retrieval experiment</p>
          <h1 className="display mt-1 text-3xl">A/B/C testing lab</h1>
          <p className="mt-2 max-w-2xl text-slate-500">
            Send an identical question set through dense, hybrid, and hybrid-reranked pipelines.
            Every arm is logged to MLflow.
          </p>
        </div>
        <button onClick={run} disabled={busy} className="flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-3 font-semibold text-white hover:bg-brand-700 disabled:opacity-50">
          {busy ? <FlaskConical className="animate-pulse" size={18} /> : <Play size={18} />}
          {busy ? 'Running 3 arms…' : 'Run experiment'}
        </button>
      </div>

      {error && <p className="mt-5 rounded-xl bg-red-50 p-3 text-red-700">{error}</p>}

      <div className="mt-7 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(400px,1.2fr)]">
        <section className="space-y-3">
          <h2 className="display text-lg">Question set</h2>
          {items.map((item, index) => (
            <div key={item.question} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
              <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
                Question {index + 1}
                <textarea value={item.question} onChange={(event) => update(index, 'question', event.target.value)} rows={2} className="mt-2 w-full resize-none rounded-lg border border-slate-200 p-2 text-sm font-normal normal-case tracking-normal outline-none focus:border-brand-500" />
              </label>
              <label className="mt-3 block text-xs font-bold uppercase tracking-wide text-slate-400">
                Ground truth
                <textarea value={item.ground_truth} onChange={(event) => update(index, 'ground_truth', event.target.value)} rows={2} className="mt-2 w-full resize-none rounded-lg border border-slate-200 p-2 text-sm font-normal normal-case tracking-normal outline-none focus:border-brand-500" />
              </label>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <h2 className="display text-lg">Strategy comparison</h2>
          <p className="text-sm text-slate-500">Higher is better; RAGAS scores shown as percentages.</p>
          <div className="mt-5 h-96">
            <ResponsiveContainer>
              <BarChart data={chart} margin={{ left: 5, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="metric" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend formatter={(value) => strategyNames[value]} />
                <Bar dataKey="dense" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="hybrid" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="hybrid_rerank" fill="#0a8567" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {results.length > 0 && (
            <div className="grid gap-2 sm:grid-cols-3">
              {results.map((result) => (
                <div key={result.strategy} className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xs font-bold text-slate-500">{strategyNames[result.strategy]}</p>
                  <p className="mt-1 text-sm">Latency: {((result.metrics.mean_latency_ms ?? 0) / 1000).toFixed(1)}s</p>
                  <p className="text-sm">Hallucination: {((result.metrics.hallucination_rate ?? 0) * 100).toFixed(1)}%</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
