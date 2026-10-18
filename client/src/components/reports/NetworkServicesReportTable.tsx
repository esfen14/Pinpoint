import { useMemo, useState } from 'react'
import { ArrowUpDown, Search } from 'lucide-react'
import { useSystemSettings } from '../../contexts/SystemSettingsContext'
import { exportRows } from '../../utils/exportData'
import { ExportMenu } from '../shared/ExportMenu'
import type { ServiceRow } from '../../types/report'
import { Pagination } from '../shared/Pagination'

type NetworkServicesReportTableProps = {
  services: ServiceRow[]
  isLoading: boolean
  observedAt?: string | null
  title?: string
}

const PAGE_SIZE = 10

export function NetworkServicesReportTable({
  services,
  isLoading,
  title = 'Network Services Report',
  observedAt = null,
}: NetworkServicesReportTableProps) {
  const { settings } = useSystemSettings()
  const [query, setQuery] = useState('')
  const [sortAsc, setSortAsc] = useState(true)
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    let result = services
    if (query.trim()) {
      const q = query.toLowerCase()
      result = result.filter((s) => s.service.toLowerCase().includes(q))
    }
    return [...result].sort((a, b) =>
      sortAsc ? a.service.localeCompare(b.service) : b.service.localeCompare(a.service)
    )
  }, [services, query, sortAsc])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, pageCount)
  const paginated = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const exportData = filtered.map((s) => ({
    Service: s.service,
    'Current status observed at': observedAt ?? '',
    'Total Instances': s.totalInstances,
    'Current OK': s.ok,
    'Current Warning': s.warning,
    'Current Critical': s.critical,
    'Current Unknown': s.unknown,
    'Current Pending': s.pending,
    'Current Unavailable': s.unavailable,
    'Availability during recorded time %': s.uptimePct ?? '',
    'Recorded time (seconds)': s.known_seconds,
    'No recorded data (seconds)': s.no_recorded_data_seconds,
    'Nagios no data (seconds)': s.no_data_seconds,
    'Engine not running (seconds)': s.nagios_not_running_seconds,
    'Unaccounted time (seconds)': s.unaccounted_seconds,
  }))

  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-sm dark:bg-[#171B20]">
      <div className="relative flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 p-4 dark:border-white/10">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 dark:border-white/10 dark:bg-[#0D1117]">
            <Search className="h-4 w-4 text-gray-500" />
            <input
              placeholder="Search service"
              value={query}
              onChange={(e) => { setQuery(e.target.value); setPage(1) }}
              className="bg-transparent text-sm text-gray-800 outline-none placeholder:text-gray-500 dark:text-white"
            />
          </div>

          <button
            type="button"
            onClick={() => setSortAsc((v) => !v)}
            title={sortAsc ? 'Sorted A → Z' : 'Sorted Z → A'}
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/10"
          >
            <ArrowUpDown className="h-4 w-4" />
          </button>

          <ExportMenu
            label
            allowedFormats={isLoading || services.length === 0 ? [] : settings.exportFormats}
            onExport={(format) => exportRows(exportData, format, 'network-services-report')}
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-275 text-left text-sm">
          <thead className="border-b border-gray-200 text-gray-500 dark:border-white/10 dark:text-gray-500">
            <tr>
              <th className="px-4 py-3">Service</th>
              <th className="px-4 py-3">Instances</th>
              <th className="px-4 py-3">Current OK</th>
              <th className="px-4 py-3">Current Warning</th>
              <th className="px-4 py-3">Current Critical</th>
              <th className="px-4 py-3">Current Unknown</th>
              <th className="px-4 py-3">Availability %</th>
              <th className="px-4 py-3">Current Pending / Unavailable</th>
              <th className="px-4 py-3">Recorded time (seconds)</th>
              <th className="px-4 py-3">No recorded data (seconds)</th>
            </tr>
          </thead>

          <tbody>
            {isLoading ? (
              <tr><td colSpan={10} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">Loading…</td></tr>
            ) : paginated.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                  {query ? 'No services match your search' : 'No data in this period'}
                </td>
              </tr>
            ) : (
              paginated.map((svc) => (
                <tr key={svc.service} className="border-b border-gray-100 hover:bg-gray-50 dark:border-white/5 dark:hover:bg-white/5">
                  <td className="px-4 py-3 text-gray-900 dark:text-white">{svc.service}</td>
                  <td className="px-4 py-3 text-gray-900 dark:text-white">{svc.totalInstances}</td>
                  <td className="px-4 py-3 text-emerald-600 dark:text-emerald-400">{svc.ok}</td>
                  <td className="px-4 py-3 text-amber-600 dark:text-amber-400">{svc.warning}</td>
                  <td className="px-4 py-3 text-red-600 dark:text-red-400">{svc.critical}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{svc.unknown}</td>
                  <td className="px-4 py-3 text-gray-900 dark:text-white">{svc.uptimePct ?? '—'}</td>
                  <td className="px-4 py-3">{svc.pending} / {svc.unavailable}</td>
                  <td className="px-4 py-3">{svc.known_seconds}</td>
                  <td className="px-4 py-3">{svc.no_recorded_data_seconds}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3 text-sm text-gray-500 dark:border-white/10 dark:text-gray-400">
        <span>Showing {filtered.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, filtered.length)} of {filtered.length} services</span>
        <Pagination page={currentPage} pageCount={pageCount} onPageChange={setPage} />
      </div>
    </div>
  )
}
