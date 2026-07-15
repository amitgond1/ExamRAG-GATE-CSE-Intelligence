import { ChevronDown, FileText } from 'lucide-react'
import type { SourceChunk } from '../types'

export default function SourceList({ sources }: { sources: SourceChunk[] }) {
  if (!sources.length) return null
  return <details className="mt-4 rounded-xl border border-slate-200 bg-slate-50"><summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm font-semibold text-slate-700"><span className="flex items-center gap-2"><FileText size={16} className="text-brand-600" />{sources.length} retrieved sources</span><ChevronDown size={16} /></summary><div className="space-y-2 border-t border-slate-200 p-3">{sources.map((source, index) => <article key={source.chunk_id} className="rounded-lg bg-white p-3 text-sm"><div className="mb-2 flex flex-wrap items-center gap-2"><span className="rounded bg-brand-100 px-2 py-0.5 font-bold text-brand-700">C{index + 1}</span><strong>{source.source}</strong><span className="text-slate-400">p. {source.page ?? '—'}</span><span className="ml-auto text-xs text-slate-400">{source.subject} · {source.topic}</span></div><p className="line-clamp-4 leading-6 text-slate-600">{source.text}</p></article>)}</div></details>
}
