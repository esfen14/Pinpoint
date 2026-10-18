import { useEffect, useMemo, useState } from 'react'
import { Bell, CheckCircle2, Server, XCircle } from 'lucide-react'

import { useSystemSettings } from '../../contexts/SystemSettingsContext'
import { apiGet, errorMessage } from '../../lib/api'
import { exportMeta, STATE_COLOR } from '../../lib/reportFormat'
import { exportRows } from '../../utils/exportData'
import { formatServerDateTime } from '../../utils/formatDateTime'
import type { AlertHistogram, AlertSummary } from '../../types/report'
import { ExportMenu } from '../shared/ExportMenu'
import { Pagination } from '../shared/Pagination'
import { ReportNotes } from './ReportNotes'
import type { ExtraReportCard } from './ExtraReports'

export type AlertDrilldown = { hostname?: string; service?: string | null; recurrence?: string }

type Props = {
  query: string
  runKey: number
  onStatus: (message: { type: 'success' | 'error'; text: string } | null) => void
  onOpenAlerts: (target: AlertDrilldown) => void
  description: string
  // Summary cards shown above the tabs, like the other reports.
  onCards?: (cards: ExtraReportCard[]) => void
}

const PAGE_SIZE = 10

// Loads one analysis endpoint for the applied query; a superseded response is discarded.
function useAnalysis<T>(path: string, query: string, runKey: number, onStatus: Props['onStatus']) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setFailed(false)
    apiGet<T>(`/api/system/report/${path}?${query}`)
      .then((result) => { if (!cancelled) { setData(result); onStatus(null) } })
      .catch((err) => {
        if (cancelled) return
        setData(null)
        setFailed(true)
        onStatus({ type: 'error', text: errorMessage(err, 'Could not run report. Please try again.') })
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, runKey])
  return { data, loading, failed }
}

function PolicyNote({ policy, period }: { policy: string; period: AlertSummary['period'] }) {
  const zone = period.time_zone
  return (
    <p>
      {policy}. {zone ? `Period and bucketing use ${zone.name} (UTC offset ${zone.utc_offset_seconds / 3600} h).` : ''}
    </p>
  )
}

export function AlertSummaryReport({ query, runKey, onStatus, onOpenAlerts, description, onCards }: Props) {
  const { settings } = useSystemSettings()
  const { data, loading } = useAnalysis<AlertSummary>('alert-summary', query, runKey, onStatus)
  const [page, setPage] = useState(1)
  useEffect(() => setPage(1), [data])

  useEffect(() => {
    const t = data?.totals
    // Same colour meaning as the other reports: gold total, green recoveries, red problems, gray scope.
    onCards?.(t ? [
      { title: 'Total Events', value: String(t.problem_events + t.recovery_events), subtitle: 'Problems and recoveries in this period', icon: Bell, gradient: 'linear-gradient(135deg,#FFB100,#F59E0B)' },
      { title: 'Recoveries', value: String(t.recovery_events), subtitle: 'Returned to OK / UP, counted separately', icon: CheckCircle2, gradient: 'linear-gradient(135deg,#22C55E,#16A34A)' },
      { title: 'Problems', value: String(t.problem_events), subtitle: `${t.host_problem_events} host, ${t.service_problem_events} service`, icon: XCircle, gradient: 'linear-gradient(135deg,#EF4444,#DC2626)' },
      { title: 'Hosts Affected', value: String(t.distinct_hosts), subtitle: `${t.distinct_objects} hosts and services in all`, icon: Server, gradient: 'linear-gradient(135deg,#6B7280,#4B5563)' },
    ] : [])
    return () => onCards?.([])
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  const ranking = data?.ranking ?? []
  const pageCount = Math.max(1, Math.ceil(ranking.length / PAGE_SIZE))
  const current = Math.min(page, pageCount)
  const rows = ranking.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE)
  const when = (ts: number) => formatServerDateTime(new Date(ts * 1000).toISOString(), settings.dateTimeFormat, settings.timeZone)
  const byService = data?.by === 'service'

  function onExport(format: Parameters<typeof exportRows>[1]) {
    if (!data) return
    exportRows(ranking.map((r) => ({
      Rank: r.rank, Host: r.hostname, Service: r.service ?? '', 'Problem events': r.total,
      States: Object.entries(r.states).map(([k, v]) => `${k} ${v}`).join('; '),
      'First event': new Date(r.first * 1000).toISOString(), 'Last event': new Date(r.last * 1000).toISOString(),
    })), format, 'alert-summary-report', exportMeta(data.period, {
      Scope: `${data.filters.scope}, grouped by ${data.by}`,
      'Event policy': data.filters.policy,
      Units: 'Counts are alert events, not outages or durations',
      Ranking: 'Event count descending, then host name, then service name',
    }, data.generated_at))
  }

  return (
    <>
    <div className="rounded-2xl bg-white shadow-sm dark:bg-[#171B20]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 p-4 dark:border-white/10">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Alert Summary</h2>
        <ExportMenu label allowedFormats={loading || !data?.complete ? [] : settings.exportFormats} onExport={onExport} />
      </div>
      {data?.notice && <p role="alert" className="px-4 pt-3 text-amber-600 dark:text-amber-400">{data.notice}</p>}

      <div className="overflow-x-auto">
        <table className="w-full min-w-175 text-left text-sm">
          <thead className="border-b border-gray-200 text-gray-500 dark:border-white/10">
            <tr>
              <th className="px-4 py-3">Rank</th>
              <th className="px-4 py-3">Host</th>
              {byService && <th className="px-4 py-3">Service</th>}
              <th className="px-4 py-3">Problem events</th>
              <th className="px-4 py-3">States</th>
              <th className="px-4 py-3">Last event</th>
              <th className="px-4 py-3">Alerts</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">Loading…</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                {data?.complete === false ? 'Totals are not shown for an incomplete result' : 'No matching alert events in this period'}
              </td></tr>
            ) : rows.map((r) => (
              <tr key={`${r.hostname}/${r.service ?? ''}`} className="border-b border-gray-100 dark:border-white/5">
                <td className="px-4 py-3">{r.rank}</td>
                <td className="px-4 py-3">{r.hostname}</td>
                {byService && <td className="px-4 py-3">{r.service ?? 'Host alerts'}</td>}
                <td className="px-4 py-3">{r.total}</td>
                <td className="px-4 py-3">{Object.entries(r.states).map(([k, v]) => `${k} ${v}`).join(', ')}</td>
                <td className="px-4 py-3">{when(r.last)}</td>
                <td className="px-4 py-3">
                  <button type="button" onClick={() => onOpenAlerts({ hostname: r.hostname, service: r.service })}
                    className="text-[#ffb100] underline">Open alerts</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3 text-sm text-gray-500 dark:border-white/10 dark:text-gray-400">
        <span>Ranked {ranking.length} {byService ? 'objects' : 'hosts'}; the first page is the top ten</span>
        <Pagination page={current} pageCount={pageCount} onPageChange={setPage} />
      </div>
    </div>
    <ReportNotes description={description}>
      {data && <PolicyNote policy={data.filters.policy} period={data.period} />}
      <p>Counts are alert events, not outages. Recoveries, when included, are counted separately. The first page of the ranking is the top ten.</p>
    </ReportNotes>
    </>
  )
}

export function AlertHistogramReport({ query, runKey, onStatus, onOpenAlerts, description }: Props) {
  const { settings } = useSystemSettings()
  const { data, loading } = useAnalysis<AlertHistogram>('alert-histogram', query, runKey, onStatus)
  const states = useMemo(() => Object.keys(data?.series ?? {}), [data])
  const buckets = data?.buckets ?? []
  const max = Math.max(1, ...buckets.map((b) => b.total))
  // Fixed-ratio chart: y axis in whole events, x labels thinned so they never overlap.
  const CHART_W = 720, CHART_H = 220, PAD_L = 34, PAD_T = 10, PAD_B = 24
  const plotH = CHART_H - PAD_T - PAD_B
  const slot = (CHART_W - PAD_L) / Math.max(1, buckets.length)
  const barW = Math.max(3, slot * 0.7)
  const labelEvery = data?.breakdown === 'hour' ? 16 : data?.breakdown === 'day_of_month' ? 5 : 1

  function onExport(format: Parameters<typeof exportRows>[1]) {
    if (!data) return
    exportRows(buckets.map((b) => ({
      Bucket: b.label, Total: b.total, ...Object.fromEntries(states.map((s) => [s, b.states[s] ?? 0])),
    })), format, 'alert-histogram-report', exportMeta(data.period, {
      Breakdown: `${data.breakdown} (recurring buckets, not a chronological history)`,
      'Event policy': data.filters.policy,
      Bucketing: data.bucketing_note,
      Units: 'Counts are alert events',
    }, data.generated_at))
  }

  const open = (index: number) => data && onOpenAlerts({ recurrence: `${data.breakdown}:${index}` })

  return (
    <>
    <div className="rounded-2xl bg-white shadow-sm dark:bg-[#171B20]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 p-4 dark:border-white/10">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Alert Histogram</h2>
        <ExportMenu label allowedFormats={loading || !data?.complete ? [] : settings.exportFormats} onExport={onExport} />
      </div>
      {data?.notice && <p role="alert" className="px-4 pt-3 text-amber-600 dark:text-amber-400">{data.notice}</p>}
      {loading && <p role="status" className="p-4 text-gray-500 dark:text-gray-400">Loading…</p>}

      {data?.complete && (
        <div className="p-4">
          <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} role="group" className="w-full"
            aria-label={`Alert histogram by ${data.breakdown.replace('_', ' ')}: ${data.total} events`}>
            <title>{`Alert histogram by ${data.breakdown.replace('_', ' ')}`}</title>
            {(max <= 1 ? [0, 1] : [0, 0.5, 1]).map((f) => {
              const y = PAD_T + plotH * (1 - f)
              return (
                <g key={f}>
                  <line x1={PAD_L} x2={CHART_W} y1={y} y2={y} stroke="currentColor" strokeOpacity={f === 0 ? 0.35 : 0.12} className="text-gray-500" />
                  <text x={PAD_L - 6} y={y + 4} textAnchor="end" fontSize="11" fill="currentColor" className="text-gray-500">{Math.round(max * f)}</text>
                </g>
              )
            })}
            {buckets.map((b, i) => {
              let y = PAD_T + plotH
              const x = PAD_L + i * slot
              return (
                <g key={b.label} role="button" tabIndex={0}
                  aria-label={`${b.label}: ${b.total} alert events. Open matching alerts`}
                  onClick={() => open(i)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i) } }}
                  className="cursor-pointer focus:outline-none [&:focus>rect:first-child]:stroke-[#ffb100] [&:hover>rect:first-child]:fill-gray-500/10">
                  <rect x={x} y={PAD_T} width={slot} height={plotH} fill="transparent" strokeWidth={1.5} stroke="transparent" />
                  {states.map((s) => {
                    const h = ((b.states[s] ?? 0) / max) * plotH
                    y -= h
                    return h > 0 ? <rect key={s} x={x + (slot - barW) / 2} y={y} width={barW} height={h} fill={STATE_COLOR[s] ?? '#6b7280'} /> : null
                  })}
                  {i % labelEvery === 0 && (
                    <text x={x + slot / 2} y={CHART_H - 6} textAnchor="middle" fontSize="11" fill="currentColor" className="text-gray-500">
                      {data.breakdown === 'weekday' ? b.label.slice(0, 3) : b.label}
                    </text>
                  )}
                </g>
              )
            })}
          </svg>
          <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[13px] text-gray-700 dark:text-gray-300">
            {states.map((s) => (
              <li key={s} className="flex items-center gap-1.5">
                <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: STATE_COLOR[s] ?? '#6b7280' }} />{s}
              </li>
            ))}
          </ul>

          <div className="mt-4 max-h-80 overflow-auto">
            <table className="w-full text-left text-sm" aria-label="Histogram bucket counts">
              <thead className="sticky top-0 bg-white text-gray-500 dark:bg-[#171B20]">
                <tr>
                  <th className="px-3 py-2">Bucket</th>
                  <th className="px-3 py-2">Total</th>
                  {states.map((s) => <th key={s} className="px-3 py-2">{s}</th>)}
                  <th className="px-3 py-2">Alerts</th>
                </tr>
              </thead>
              <tbody>
                {buckets.map((b, i) => (
                  <tr key={b.label} className="border-b border-gray-100 dark:border-white/5">
                    <td className="px-3 py-2">{b.label}</td>
                    <td className="px-3 py-2">{b.total}</td>
                    {states.map((s) => <td key={s} className="px-3 py-2">{b.states[s] ?? 0}</td>)}
                    <td className="px-3 py-2">
                      {b.total > 0 && <button type="button" onClick={() => open(i)} className="text-[#ffb100] underline">Open alerts</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
    <ReportNotes description={description}>
      {data && <PolicyNote policy={data.filters.policy} period={data.period} />}
      {data && <p>{data.bucketing_note} These are recurring buckets, not a chronological chart.</p>}
    </ReportNotes>
    </>
  )
}
