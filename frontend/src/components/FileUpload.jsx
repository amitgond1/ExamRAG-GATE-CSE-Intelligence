import { AlertCircle, CheckCircle2, LoaderCircle, Server, Upload } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { checkBackend, uploadPdf } from '../api'

export default function FileUpload() {
  const input = useRef(null)
  const [status, setStatus] = useState('')
  const [state, setState] = useState('idle')
  const [connected, setConnected] = useState(null)

  useEffect(() => { checkBackend().then(setConnected) }, [])

  async function upload(file) {
    if (!file) return
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setState('error'); setStatus('Please select a PDF file.'); return
    }
    if (file.size > 50 * 1024 * 1024) {
      setState('error'); setStatus('PDF must be smaller than 50 MB.'); return
    }
    setState('busy'); setStatus(`Indexing ${file.name}…`)
    try {
      const result = await uploadPdf(file)
      setConnected(true); setState('success')
      setStatus(`${result.chunks_created} chunks indexed · ${result.subjects_detected.join(', ')}`)
    } catch (error) {
      setState('error')
      setStatus(error instanceof Error ? error.message : 'Upload failed')
      setConnected(await checkBackend())
    } finally {
      if (input.current) input.current.value = ''
    }
  }

  function drop(event) {
    event.preventDefault(); upload(event.dataTransfer.files[0])
  }

  const busy = state === 'busy'
  return <div className="space-y-2">
    <div className={`flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs font-semibold ${connected === true ? 'bg-brand-50 text-brand-700' : connected === false ? 'bg-red-50 text-red-700' : 'bg-slate-100 text-slate-500'}`}>
      <Server size={14} />{connected === true ? 'ExamRAG backend connected' : connected === false ? 'Backend offline on port 8001' : 'Checking backend…'}
    </div>
    <input ref={input} type="file" accept="application/pdf" className="hidden" onChange={(event) => upload(event.target.files?.[0])} />
    <button type="button" disabled={busy || connected === false} onClick={() => input.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={drop} className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 px-3 py-3 text-sm font-semibold text-slate-600 hover:border-brand-500 hover:text-brand-700 disabled:cursor-not-allowed disabled:opacity-50">
      {busy ? <LoaderCircle className="animate-spin" size={17} /> : <Upload size={17} />}{busy ? 'Processing PDF…' : 'Upload PDF'}
    </button>
    {status && <p className={`flex items-start gap-1.5 text-xs leading-5 ${state === 'error' ? 'text-red-700' : state === 'success' ? 'text-brand-700' : 'text-slate-500'}`}>{state === 'error' ? <AlertCircle className="mt-0.5 shrink-0" size={14} /> : state === 'success' ? <CheckCircle2 className="mt-0.5 shrink-0" size={14} /> : null}<span>{status}</span></p>}
  </div>
}
