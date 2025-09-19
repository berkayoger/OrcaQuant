import type { ChangeEvent } from 'react'

type Props = {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

export default function Pagination({ page, pageSize, total, onPageChange, onPageSizeChange }: Props) {
  const pageCount = Math.max(1, Math.ceil(total / Math.max(pageSize, 1)))

  function handlePageSizeChange(event: ChangeEvent<HTMLSelectElement>) {
    const value = Number(event.target.value)
    onPageSizeChange(value)
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-neutral-900 border-t border-neutral-800">
      <div className="flex items-center gap-2">
        <button
          className="btn"
          disabled={page <= 1}
          onClick={() => onPageChange(Math.max(1, page - 1))}
        >
          Önceki
        </button>
        <span className="text-sm opacity-80">
          Sayfa {page} / {pageCount}
        </span>
        <button
          className="btn"
          disabled={page >= pageCount}
          onClick={() => onPageChange(Math.min(pageCount, page + 1))}
        >
          Sonraki
        </button>
      </div>
      <div className="flex items-center gap-2 text-sm opacity-80">
        <span>Sayfa boyutu</span>
        <select className="input" value={pageSize} onChange={handlePageSizeChange}>
          {[10, 20, 50, 100].map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
