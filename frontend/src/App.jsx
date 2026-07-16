import { BarChart3, BookOpenCheck, FlaskConical, MessageSquareText } from 'lucide-react'
import { lazy, Suspense } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'

const Chat = lazy(() => import('./pages/Chat'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const ABTesting = lazy(() => import('./pages/ABTesting'))

const nav = [
  { to: '/', label: 'Tutor', icon: MessageSquareText },
  { to: '/evaluation', label: 'Evaluation', icon: BarChart3 },
  { to: '/experiments', label: 'A/B Lab', icon: FlaskConical },
]

export default function App() {
  return (
    <div className="min-h-screen grid-bg">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 sm:bg-white/90 sm:backdrop-blur">
        <div className="mx-auto flex min-w-0 max-w-7xl items-center justify-between gap-2 px-3 py-2.5 sm:px-6 sm:py-3">
          <NavLink to="/" className="flex min-w-0 items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-600 text-white"><BookOpenCheck size={20} /></span>
            <span><strong className="display block leading-4">ExamRAG</strong><small className="hidden text-xs text-slate-500 sm:block">GATE CSE intelligence</small></span>
          </NavLink>
          <nav className="fixed inset-x-0 bottom-0 z-30 flex justify-around gap-1 border-t border-slate-200 bg-white/95 p-2 shadow-[0_-8px_24px_rgba(16,24,40,0.08)] backdrop-blur sm:static sm:shrink-0 sm:justify-start sm:rounded-xl sm:border-0 sm:bg-slate-100 sm:p-1 sm:shadow-none">
            {nav.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} end={to === '/'} aria-label={label} className={({ isActive }) => `flex min-h-11 min-w-20 items-center justify-center gap-1.5 rounded-lg px-2 py-2 text-xs font-semibold transition sm:min-h-10 sm:min-w-10 sm:gap-2 sm:px-3 sm:text-sm ${isActive ? 'bg-brand-50 text-brand-700 sm:bg-white sm:shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}>
                <Icon size={16} /><span>{label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full min-w-0 max-w-[100vw] overflow-x-hidden px-2 py-3 pb-24 sm:max-w-7xl sm:px-6 sm:py-7"><Suspense fallback={<div className="grid min-h-[60vh] place-items-center text-sm font-semibold text-slate-500">Loading workspace…</div>}><Routes><Route path="/" element={<Chat />} /><Route path="/evaluation" element={<Dashboard />} /><Route path="/experiments" element={<ABTesting />} /></Routes></Suspense></main>
    </div>
  )
}
