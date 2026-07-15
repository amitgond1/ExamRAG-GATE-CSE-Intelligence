import type { EvaluationItem, EvaluationRun, SourceChunk, Strategy } from './types'

const API = import.meta.env.VITE_API_URL ?? '/api'

export async function checkBackend(): Promise<boolean> {
  try {
    const response = await fetch(`${API}/health`, { signal: AbortSignal.timeout(4000) })
    if (!response.ok) return false
    const body = await response.json()
    return body.service === 'ExamRAG'
  } catch {
    return false
  }
}

async function errorFrom(response: Response): Promise<Error> {
  try { const body = await response.json(); return new Error(body.detail ?? 'Request failed') }
  catch { return new Error(`Request failed (${response.status})`) }
}

export async function streamChat(
  question: string,
  strategy: Strategy,
  handlers: { onSources: (sources: SourceChunk[]) => void; onToken: (token: string) => void; onDone: (latency: number) => void },
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API}/chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, signal,
    body: JSON.stringify({ question, strategy, stream: true }),
  })
  if (!response.ok) throw await errorFrom(response)
  if (!response.body) throw new Error('Streaming is not supported by this browser')

  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''
  while (true) {
    const { value, done } = await reader.read(); buffer += decoder.decode(value, { stream: !done })
    const events = buffer.split('\n\n'); buffer = events.pop() ?? ''
    for (const raw of events) {
      let event = 'message'; let data = ''
      for (const line of raw.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      if (!data) continue
      const parsed = JSON.parse(data)
      if (event === 'sources') handlers.onSources(parsed)
      else if (event === 'token') handlers.onToken(parsed.text)
      else if (event === 'done') handlers.onDone(parsed.latency_ms)
      else if (event === 'error') throw new Error(parsed.detail)
    }
    if (done) break
  }
}

export async function fetchHistory(): Promise<EvaluationRun[]> {
  const response = await fetch(`${API}/eval-history`)
  if (!response.ok) throw await errorFrom(response)
  return response.json()
}

export async function runABTest(items: EvaluationItem[]) {
  const response = await fetch(`${API}/ab-test`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items, run_name: `dashboard-${new Date().toISOString()}` }),
  })
  if (!response.ok) throw await errorFrom(response)
  return response.json()
}

export async function uploadPdf(file: File): Promise<{ chunks_created: number; subjects_detected: string[] }> {
  const body = new FormData(); body.append('file', file)
  const response = await fetch(`${API}/ingest`, { method: 'POST', body })
  if (!response.ok) throw await errorFrom(response)
  return response.json()
}
