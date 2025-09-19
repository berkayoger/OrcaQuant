import { useState } from 'react'

type Filters = {
  from?: string
  to?: string
  status?: string
  plan?: string
}

type Props = {
  onFiltersChange: (filters: Filters) => void
}

export function AdvancedFilters({ onFiltersChange }: Props) {
  const [from, setFrom] = useState<string>()
  const [to, setTo] = useState<string>()
  const [status, setStatus] = useState<string>()
  const [plan, setPlan] = useState<string>()

  function apply() {
    onFiltersChange({ from, to, status, plan })
  }

  function reset() {
    setFrom(undefined)
    setTo(undefined)
    setStatus(undefined)
    setPlan(undefined)
    onFiltersChange({})
  }

  return (
    <div className="card space-y-4">
      <h3 className="font-medium">Gelişmiş Filtreler</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm mb-1">Başlangıç</label>
          <input
            type="date"
            className="input"
            value={from || ''}
            onChange={(event) => setFrom(event.target.value || undefined)}
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Bitiş</label>
          <input
            type="date"
            className="input"
            value={to || ''}
            onChange={(event) => setTo(event.target.value || undefined)}
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Durum</label>
          <select
            className="input"
            value={status || ''}
            onChange={(event) => setStatus(event.target.value || undefined)}
          >
            <option value="">Hepsi</option>
            <option value="active">Aktif</option>
            <option value="blocked">Engelli</option>
            <option value="pending">Bekleyen</option>
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1">Plan</label>
          <select
            className="input"
            value={plan || ''}
            onChange={(event) => setPlan(event.target.value || undefined)}
          >
            <option value="">Hepsi</option>
            <option value="free">Free</option>
            <option value="basic">Basic</option>
            <option value="premium">Premium</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
      </div>
      <div className="flex gap-2">
        <button onClick={apply} className="btn">
          Uygula
        </button>
        <button onClick={reset} className="btn" style={{ background: '#4b5563' }}>
          Temizle
        </button>
      </div>
    </div>
  )
}
