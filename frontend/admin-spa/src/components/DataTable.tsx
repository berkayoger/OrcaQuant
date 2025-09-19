import { useMemo, useState } from 'react'
import type { ColumnDef, SortingState, Updater } from '@tanstack/react-table'
import { flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'
import Pagination from './Pagination'

type SortPayload = { id: string; desc: boolean }

type Props<T> = {
  data: T[]
  columns: ColumnDef<T, any>[]
  manualSort?: boolean
  onSortChange?: (sort: SortPayload | null) => void
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
  withSelection?: boolean
  selectedRows?: number[]
  onSelectionChange?: (rows: number[]) => void
}

export default function DataTable<T>({
  data,
  columns,
  manualSort,
  onSortChange,
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  withSelection,
  selectedRows,
  onSelectionChange
}: Props<T>) {
  const [sorting, setSorting] = useState<SortingState>([])

  const finalCols = useMemo<ColumnDef<T, any>[]>(() => {
    if (!withSelection) return columns

    const selectionColumn: ColumnDef<T, any> = {
      id: '__select__',
      header: () => (
        <input
          type="checkbox"
          aria-label="Tümünü seç"
          checked={!!selectedRows && selectedRows.length === data.length && data.length > 0}
          onChange={(event) =>
            onSelectionChange?.(
              event.target.checked ? data.map((_, index) => index) : []
            )
          }
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          aria-label="Seç"
          checked={!!selectedRows?.includes(row.index)}
          onChange={(event) => {
            if (!onSelectionChange) return
            const current = new Set(selectedRows || [])
            if (event.target.checked) {
              current.add(row.index)
            } else {
              current.delete(row.index)
            }
            onSelectionChange(Array.from(current).sort((a, b) => a - b))
          }}
        />
      ),
      size: 32
    }

    return [selectionColumn, ...columns]
  }, [columns, withSelection, selectedRows, data, onSelectionChange])

  const table = useReactTable<T>({
    data,
    columns: finalCols,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: manualSort,
    state: { sorting },
    onSortingChange: (updater: Updater<SortingState>) => {
      const next = typeof updater === 'function' ? updater(sorting) : updater
      setSorting(next)
      if (!onSortChange) return
      const first = next[0]
      onSortChange(first ? { id: first.id, desc: first.desc ?? false } : null)
    }
  })

  const pageCount = Math.max(1, Math.ceil((total || 0) / Math.max(1, pageSize)))

  return (
    <div className="overflow-auto rounded-lg border border-neutral-800">
      <table className="w-full text-sm">
        <thead className="bg-neutral-900/70">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="px-4 py-3 text-left font-medium text-neutral-300">
                  {header.isPlaceholder ? null : (
                    <div
                      className={header.column.getCanSort() ? 'cursor-pointer select-none' : ''}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </div>
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="border-t border-neutral-800 hover:bg-neutral-800/60">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
          {data.length === 0 && (
            <tr>
              <td colSpan={finalCols.length} className="px-4 py-6 text-center text-neutral-400">
                Kayıt bulunamadı.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <Pagination
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />
      <div className="px-4 py-2 text-xs text-neutral-500 border-t border-neutral-800">
        Toplam {total} kayıt • Sayfa {page} / {pageCount}
      </div>
    </div>
  )
}
