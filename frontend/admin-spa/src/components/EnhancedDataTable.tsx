import { useMemo, useState } from 'react'
import DataTable from './DataTable'
import toast from 'react-hot-toast'

type ExportFormat = 'csv' | 'excel'

type EnhancedTableProps<T> = {
  data: T[]
  columns: any[]
  onBulkAction?: (action: 'delete' | 'export', rows: number[]) => void
  exportOptions?: ExportFormat[]
}

export function EnhancedDataTable<T>({
  data,
  columns,
  onBulkAction,
  exportOptions = ['csv', 'excel']
}: EnhancedTableProps<T>) {
  const [selectedRows, setSelectedRows] = useState<number[]>([])

  const tableColumns = useMemo(() => columns, [columns])

  function exportData(format: ExportFormat) {
    if (!data.length) {
      toast('Dışa aktarılacak veri yok')
      return
    }
    const csv = toCsv(data as any[])
    const blob = new Blob([csv], {
      type: format === 'excel' ? 'application/vnd.ms-excel' : 'text/csv;charset=utf-8;'
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `export.${format === 'excel' ? 'xls' : 'csv'}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      {selectedRows.length > 0 && (
        <div className="flex items-center gap-2 p-3 bg-blue-900/20 rounded border border-blue-500/50">
          <span className="text-sm">{selectedRows.length} öğe seçildi</span>
          <button
            onClick={() => onBulkAction?.('delete', selectedRows)}
            className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-sm"
          >
            Sil
          </button>
          <button
            onClick={() => onBulkAction?.('export', selectedRows)}
            className="px-3 py-1 bg-green-600 hover:bg-green-500 rounded text-sm"
          >
            Dışa Aktar (Seçili)
          </button>
        </div>
      )}

      <div className="flex gap-2">
        {exportOptions.map((format) => (
          <button
            key={format}
            onClick={() => exportData(format)}
            className="px-3 py-1 bg-neutral-800 hover:bg-neutral-700 rounded text-sm"
          >
            {format.toUpperCase()} İndir
          </button>
        ))}
        <button
          onClick={() => {
            setSelectedRows([])
            toast('Seçimler temizlendi')
          }}
          className="px-3 py-1 bg-neutral-800 hover:bg-neutral-700 rounded text-sm"
        >
          Seçimleri Temizle
        </button>
      </div>

      <DataTable
        data={data}
        columns={tableColumns}
        withSelection
        selectedRows={selectedRows}
        onSelectionChange={setSelectedRows}
        page={1}
        pageSize={data.length || 10}
        total={data.length || 0}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
      />
    </div>
  )
}

function toCsv(rows: any[]) {
  if (!rows?.length) return ''
  const headers = Object.keys(rows[0])
  const csvRows = [headers.join(',')]
  for (const row of rows) {
    const values = headers.map((header) => {
      const value = row[header] ?? ''
      const stringValue = String(value).replace(/"/g, '""')
      return `"${stringValue}"`
    })
    csvRows.push(values.join(','))
  }
  return csvRows.join('\n')
}
