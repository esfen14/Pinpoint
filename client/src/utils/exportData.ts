import type { ExportFormat } from '../types/settings'
import { apiPost } from '../lib/api'

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/** Report context written above the data: period, scope, time zone, source, units, warnings. */
export type ExportMeta = Record<string, string>

function escapeHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function escapeCsvCell(value: unknown): string {
  const str = String(value ?? '')
  return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str
}

function exportCsv(rows: Record<string, unknown>[], filename: string, meta?: ExportMeta) {
  const metaLines = meta ? [...Object.entries(meta).map(([k, v]) => `# ${k}: ${v.replace(/\n/g, ' ')}`), ''] : []
  if (rows.length === 0) {
    downloadBlob(new Blob([metaLines.join('\n')], { type: 'text/csv' }), `${filename}.csv`)
    return
  }

  const headers = Object.keys(rows[0])
  const lines = [
    ...metaLines,
    headers.join(','),
    ...rows.map((row) => headers.map((h) => escapeCsvCell(row[h])).join(',')),
  ]

  downloadBlob(
    new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' }),
    `${filename}.csv`
  )
}

// Excel opens an HTML table saved with a .xls extension and the ms-excel
// MIME type just fine — a well-established trick that avoids needing a
// spreadsheet-generation library for a "real" .xls download.
function exportXls(rows: Record<string, unknown>[], filename: string, meta?: ExportMeta) {
  const headers = rows.length > 0 ? Object.keys(rows[0]) : []
  const metaRows = meta
    ? Object.entries(meta).map(([k, v]) => `<tr><th>${escapeHtml(k)}</th><td>${escapeHtml(v)}</td></tr>`).join('')
    : ''

  const table = `
    <table>
      ${metaRows}
      <thead><tr>${headers.map((h) => `<th>${escapeHtml(h)}</th>`).join('')}</tr></thead>
      <tbody>
        ${rows
          .map(
            (row) =>
              `<tr>${headers.map((h) => `<td>${escapeHtml(row[h])}</td>`).join('')}</tr>`
          )
          .join('')}
      </tbody>
    </table>
  `

  downloadBlob(
    new Blob([table], { type: 'application/vnd.ms-excel' }),
    `${filename}.xls`
  )
}

// No PDF-generation library is installed, so PDF export opens a
// print-formatted view and lets the browser's own "Save as PDF" print
// target produce the file — a standard, dependency-free pattern.
function exportPdf(rows: Record<string, unknown>[], filename: string, meta?: ExportMeta) {
  const headers = rows.length > 0 ? Object.keys(rows[0]) : []

  const win = window.open('', '_blank')
  if (!win) return

  win.document.write(`
    <html>
      <head>
        <title>${escapeHtml(filename)}</title>
        <style>
          body { font-family: sans-serif; padding: 24px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; font-size: 12px; }
          th { background: #f3f4f6; }
        </style>
      </head>
      <body>
        <h2>${escapeHtml(filename)}</h2>
        ${meta ? `<dl style="font-size:12px">${Object.entries(meta).map(([k, v]) => `<dt style="font-weight:bold">${escapeHtml(k)}</dt><dd style="margin:0 0 4px 0">${escapeHtml(v)}</dd>`).join('')}</dl>` : ''}
        <table>
          <thead><tr>${headers.map((h) => `<th>${escapeHtml(h)}</th>`).join('')}</tr></thead>
          <tbody>
            ${rows
              .map(
                (row) =>
                  `<tr>${headers.map((h) => `<td>${escapeHtml(row[h])}</td>`).join('')}</tr>`
              )
              .join('')}
          </tbody>
        </table>
      </body>
    </html>
  `)
  win.document.close()
  win.focus()
  win.print()
}

/** Exports rows in the given format, triggering a real browser download (or print dialog for PDF). */
export function exportRows(
  rows: Record<string, unknown>[],
  format: ExportFormat,
  filename: string,
  meta?: ExportMeta
) {
  switch (format) {
    case 'CSV':
      exportCsv(rows, filename, meta)
      break
    case 'XLS':
      exportXls(rows, filename, meta)
      break
    case 'PDF':
      exportPdf(rows, filename, meta)
      break
  }

  // Fire-and-forget: record the export for the audit trail. Exports are
  // generated entirely client-side, so this is the only point the backend
  // ever finds out one happened — never let a logging failure block or
  // surface an error for the download itself.
  apiPost('/api/system/exportlog', { report_type: filename, format }).catch(() => {})
}
