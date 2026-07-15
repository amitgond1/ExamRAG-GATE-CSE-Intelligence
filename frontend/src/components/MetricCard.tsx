interface Props { label: string; value?: number | null; detail: string; inverse?: boolean }

export default function MetricCard({ label, value, detail, inverse }: Props) {
  const display = value == null ? '—' : `${(value * (inverse ? 1 : 100)).toFixed(inverse ? 2 : 1)}${inverse ? '' : '%'}`
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card"><p className="text-sm font-semibold text-slate-500">{label}</p><p className="display mt-2 text-3xl text-ink">{display}</p><p className="mt-2 text-xs leading-5 text-slate-500">{detail}</p></div>
}
