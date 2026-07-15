import { ArrowUp, Bot, Database, UserRound } from 'lucide-react'
import { FormEvent, useRef, useState } from 'react'
import { streamChat } from '../api'
import FileUpload from '../components/FileUpload'
import SourceList from '../components/SourceList'
import type { SourceChunk, Strategy } from '../types'

interface Message { id: string; role: 'user' | 'assistant'; text: string; sources?: SourceChunk[]; latency?: number; error?: boolean }
const suggestions = ['Explain deadlock prevention vs avoidance', 'What makes a schedule conflict serializable?', 'Derive the time complexity of merge sort']

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]); const [question, setQuestion] = useState(''); const [strategy, setStrategy] = useState<Strategy>('hybrid_rerank'); const [loading, setLoading] = useState(false); const controller = useRef<AbortController | null>(null)
  async function submit(event?: FormEvent, suggested?: string) {
    event?.preventDefault(); const prompt = (suggested ?? question).trim(); if (!prompt || loading) return
    const user: Message = { id: crypto.randomUUID(), role: 'user', text: prompt }; const assistantId = crypto.randomUUID()
    setMessages((old) => [...old, user, { id: assistantId, role: 'assistant', text: '' }]); setQuestion(''); setLoading(true); controller.current = new AbortController()
    try { await streamChat(prompt, strategy, { onSources: (sources) => setMessages((old) => old.map((m) => m.id === assistantId ? { ...m, sources } : m)), onToken: (token) => setMessages((old) => old.map((m) => m.id === assistantId ? { ...m, text: m.text + token } : m)), onDone: (latency) => setMessages((old) => old.map((m) => m.id === assistantId ? { ...m, latency } : m)) }, controller.current.signal) }
    catch (error) { setMessages((old) => old.map((m) => m.id === assistantId ? { ...m, text: error instanceof Error ? error.message : 'Unable to answer', error: true } : m)) }
    finally { setLoading(false) }
  }
  return <div className="grid w-full min-w-0 gap-3 sm:gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
    <aside className="min-w-0 space-y-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-card sm:p-4 lg:sticky lg:top-24 lg:self-start lg:border-0 lg:bg-transparent lg:p-0 lg:shadow-none">
      <div className="flex items-end justify-between gap-3 lg:block"><div><p className="display text-lg sm:text-xl">Retrieval setup</p><p className="hidden text-sm text-slate-500 sm:block">Choose how evidence is found.</p></div><Database size={18} className="mb-1 text-brand-600 lg:hidden" /></div>
      <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">Strategy<select value={strategy} onChange={(e) => setStrategy(e.target.value as Strategy)} className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-500 sm:mt-2 sm:py-3"><option value="dense">A · Dense top-5</option><option value="hybrid">B · Hybrid top-10</option><option value="hybrid_rerank">C · Hybrid + rerank</option></select></label>
      <FileUpload />
      <div className="hidden rounded-xl bg-brand-50 p-3 text-xs leading-5 text-brand-700 lg:block"><Database size={16} className="mb-1" />Answers are constrained to indexed PDFs and include chunk citations.</div>
    </aside>
    <section className="flex min-w-0 min-h-[calc(100dvh-19rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card sm:min-h-[70vh] sm:rounded-3xl">
      <div className="border-b border-slate-100 px-4 py-3 sm:px-6 sm:py-4"><h1 className="display text-lg sm:text-xl">GATE CSE Tutor</h1><p className="text-xs text-slate-500 sm:text-sm">Grounded answers, inspectable evidence.</p></div>
      <div className="min-w-0 flex-1 space-y-4 overflow-y-auto p-3 sm:space-y-6 sm:p-7">{messages.length === 0 && <div className="mx-auto min-w-0 max-w-xl py-8 text-center sm:py-16"><span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-brand-100 text-brand-700 sm:h-14 sm:w-14"><Bot /></span><h2 className="display mt-4 text-xl sm:mt-5 sm:text-2xl">What are you studying?</h2><p className="mx-auto mt-2 max-w-md text-sm text-slate-500 sm:text-base">Upload notes, then ask a concept or exam-style question.</p><div className="mt-5 grid min-w-0 gap-2 sm:mt-6 sm:flex sm:flex-wrap sm:justify-center">{suggestions.map((text) => <button key={text} onClick={() => submit(undefined, text)} className="min-w-0 whitespace-normal rounded-xl border border-slate-200 px-3 py-2 text-left text-xs text-slate-600 hover:border-brand-500 sm:rounded-full sm:text-center sm:text-sm">{text}</button>)}</div></div>}{messages.map((message) => <div key={message.id} className={`flex min-w-0 gap-2 sm:gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}>{message.role === 'assistant' && <span className="hidden h-8 w-8 shrink-0 place-items-center rounded-lg bg-brand-100 text-brand-700 sm:grid"><Bot size={17} /></span>}<div className={`min-w-0 max-w-[88%] break-words rounded-2xl px-3 py-2.5 text-sm sm:max-w-3xl sm:px-4 sm:py-3 sm:text-base ${message.role === 'user' ? 'bg-ink text-white' : message.error ? 'bg-red-50 text-red-700' : 'bg-slate-50 text-slate-700'}`}><p className={`whitespace-pre-wrap leading-6 sm:leading-7 ${loading && message.role === 'assistant' && !message.latency ? 'stream-cursor' : ''}`}>{message.text}</p>{message.sources && <SourceList sources={message.sources} />}{message.latency != null && <p className="mt-2 text-right text-xs text-slate-400">{(message.latency / 1000).toFixed(1)}s · {strategy}</p>}</div>{message.role === 'user' && <span className="hidden h-8 w-8 shrink-0 place-items-center rounded-lg bg-slate-200 sm:grid"><UserRound size={17} /></span>}</div>)}</div>
      <form onSubmit={submit} className="border-t border-slate-100 p-2.5 sm:p-4"><div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-white p-2 focus-within:border-brand-500 sm:rounded-2xl"><textarea value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() } }} rows={2} placeholder="Ask a GATE CSE question…" className="max-h-32 min-w-0 flex-1 resize-none px-2 py-1 text-sm outline-none sm:text-base" /><button aria-label="Send question" disabled={loading || !question.trim()} className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-600 text-white hover:bg-brand-700 disabled:bg-slate-300"><ArrowUp size={19} /></button></div></form>
    </section>
  </div>
}
