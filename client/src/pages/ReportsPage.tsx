import { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, CheckCircle2, XCircle, Loader2, SlidersHorizontal } from 'lucide-react'

import { PageHeader } from '../components/shared/PageHeader'
import { SummaryStatCard } from '../components/shared/SummaryStatCard'
import { HostAvailabilityReportTable } from '../components/reports/HostAvailabilityReportTable'
import { NetworkServicesReportTable } from '../components/reports/NetworkServicesReportTable'
import { ServiceReportContext } from '../components/reports/ServiceReportContext'
import { ReportNotes } from '../components/reports/ReportNotes'
import { AvailabilityDetailDrawer } from '../components/reports/AvailabilityDetailDrawer'
import { AlertHistogramReport, AlertSummaryReport, type AlertDrilldown } from '../components/reports/AlertAnalysisReports'
import { ExtraReports, type ExtraReportCard, type ExtraReportView } from '../components/reports/ExtraReports'
import { apiGet, errorMessage } from '../lib/api'
import { exportMeta, formatDuration } from '../lib/reportFormat'
import {
  fromHostAvailabilityResponse,
  fromNetworkServicesResponse,
  type EventScope,
  type EventStateType,
  type HistogramBreakdown,
  type HostAvailabilityReport,
  type NetworkServicesReport,
  type ReportPeriod,
} from '../types/report'

type ReportView = 'availability' | 'network-services' | 'alert-summary' | 'alert-histogram' | ExtraReportView

// Views with summary cards first, then the views without, so the tab row reads uniformly.
const VIEW_TABS: { value: ReportView; label: string; description: string }[] = [
  { value: 'availability', label: 'Host Availability', description: 'Host uptime and availability reported by Nagios archive data.' },
  { value: 'network-services', label: 'Network Services', description: 'Service health across every monitored host, aggregated by service name.' },
  { value: 'alerts', label: 'Alerts', description: 'Alert state changes recorded by Nagios during the period.' },
  { value: 'alert-summary', label: 'Alert Summary', description: 'Problem-event totals and the objects that produce the most alerts.' },
  { value: 'notifications', label: 'Notifications', description: 'Notifications Nagios sent during the period.' },
  { value: 'hosts-by-os', label: 'Hosts by OS', description: 'Host availability grouped by operating system.' },
  { value: 'device-services', label: 'Device Services', description: 'Service health for each monitored device.' },
  { value: 'alert-histogram', label: 'Alert Histogram', description: 'When alerts recur: by month, day of month, weekday or time of day.' },
]

const PERIOD_OPTIONS: { value: ReportPeriod; label: string }[] = [
  { value: 'last_24h', label: 'Last 24 hours' },
  { value: 'today', label: 'Today' },
  { value: 'last_7d', label: 'Last 7 days' },
  { value: 'last_30d', label: 'Last 30 days' },
  { value: 'last_90d', label: 'Last 90 days' },
  { value: 'custom', label: 'Custom range' },
]

// What each view can be scoped by. Controls that a view cannot honour are disabled, not ignored.
const SUPPORTS_HOST: ReportView[] = ['availability', 'hosts-by-os', 'alerts', 'notifications', 'alert-summary', 'alert-histogram']
const SUPPORTS_SERVICE: ReportView[] = ['alerts', 'notifications', 'alert-summary', 'alert-histogram']
const SUPPORTS_STATE_TYPE: ReportView[] = ['alerts', 'alert-summary', 'alert-histogram']
const SUPPORTS_RECOVERIES: ReportView[] = ['alert-summary', 'alert-histogram']
const SUPPORTS_SCOPE: ReportView[] = ['alerts', 'notifications', 'alert-summary', 'alert-histogram']

// Controls edit the draft; Run Report copies it into the applied query. Loading and exports use only the applied one.
type Query = {
  period: ReportPeriod
  customStart: string
  customEnd: string
  hostname: string
  service: string
  scope: EventScope
  stateType: EventStateType
  includeRecoveries: boolean
  contact: string
  by: 'host' | 'service'
  breakdown: HistogramBreakdown
  recurrence: string
}

const DEFAULT_QUERY: Query = {
  period: 'last_24h', customStart: '', customEnd: '', hostname: '', service: '', scope: 'both',
  stateType: 'default', includeRecoveries: false, contact: '', by: 'service', breakdown: 'hour', recurrence: '',
}

function periodQuery(q: Query) {
  const params = new URLSearchParams({ period: q.period })
  if (q.period === 'custom') {
    if (q.customStart) params.set('start', q.customStart)
    if (q.customEnd) params.set('end', q.customEnd)
  }
  return params
}

// The query string for one view: only parameters that view understands, empty ones left out.
function buildViewQuery(view: ReportView, q: Query) {
  const params = periodQuery(q)
  if (SUPPORTS_HOST.includes(view) && q.hostname.trim()) params.set('hostname', q.hostname.trim())
  if (SUPPORTS_SERVICE.includes(view) && q.hostname.trim() && q.service.trim()) params.set('service', q.service.trim())
  if (SUPPORTS_SCOPE.includes(view) && q.scope !== 'both') params.set('scope', q.scope)
  if (SUPPORTS_STATE_TYPE.includes(view) && q.stateType !== 'default') params.set('state_type', q.stateType)
  if (SUPPORTS_RECOVERIES.includes(view) && q.includeRecoveries) params.set('include_recoveries', 'true')
  if (view === 'notifications' && q.contact.trim()) params.set('contact', q.contact.trim())
  if (view === 'alert-summary') params.set('by', q.by)
  if (view === 'alert-histogram') params.set('breakdown', q.breakdown)
  if (view === 'alerts' && q.recurrence) params.set('recurrence', q.recurrence)
  return params.toString()
}

// Filter fields (not the period) and their defaults, for Clear filters.
const FILTER_DEFAULTS: Partial<Query> = {
  hostname: '', service: '', scope: 'both', stateType: 'default', includeRecoveries: false, contact: '', recurrence: '',
}

const FIELD = 'h-10 rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-sm text-[var(--text)] outline-none transition duration-200 focus:border-[#ffb100] disabled:cursor-not-allowed disabled:opacity-50'

export function ReportsPage() {
  const [view, setView] = useState<ReportView>('availability')
  const [draft, setDraft] = useState<Query>(DEFAULT_QUERY)
  const [applied, setApplied] = useState<Query>(DEFAULT_QUERY)
  const [showFilters, setShowFilters] = useState(false)

  const [availability, setAvailability] = useState<HostAvailabilityReport | null>(null)
  const [networkServices, setNetworkServices] = useState<NetworkServicesReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [stale, setStale] = useState(false)
  const [runKey, setRunKey] = useState(0)
  const [extraCards, setExtraCards] = useState<ExtraReportCard[]>([])
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [detailTarget, setDetailTarget] = useState<{ hostname: string; service: string | null } | null>(null)

  const patch = (change: Partial<Query>) => setDraft((d) => ({ ...d, ...change }))
  const clearFilters = () => patch(FILTER_DEFAULTS)
  const draftHasFilters = (Object.keys(FILTER_DEFAULTS) as (keyof Query)[]).some((k) => draft[k] !== FILTER_DEFAULTS[k])
  const customIncomplete = (q: Query) => q.period === 'custom' && (!q.customStart || !q.customEnd)

  const hasUnappliedChanges = (Object.keys(DEFAULT_QUERY) as (keyof Query)[]).some((key) => {
    if (key === 'customStart' || key === 'customEnd') return draft.period === 'custom' && draft[key] !== applied[key]
    return draft[key] !== applied[key]
  })

  // Hosts/services known from loaded reports feed the searchable pickers; free text stays possible.
  const hostOptions = useMemo(() => {
    const names = new Set<string>(availability?.hosts.map((h) => h.hostname) ?? [])
    networkServices?.services.forEach((s) => s.instances.forEach((i) => names.add(i.hostname)))
    return [...names].sort()
  }, [availability, networkServices])
  const serviceOptions = useMemo(() => {
    const names = new Set<string>()
    networkServices?.services.forEach((s) => {
      if (!draft.hostname || s.instances.some((i) => i.hostname === draft.hostname)) names.add(s.service)
    })
    return [...names].sort()
  }, [networkServices, draft.hostname])

  const requestSequence = useRef(0)

  async function loadReport(showStatus = false, source: Query = applied) {
    const sequence = ++requestSequence.current
    if (view === 'network-services') setNetworkServices(null)
    if (customIncomplete(source)) {
      setIsLoading(false)
      setStatusMessage({ type: 'error', text: 'Pick a start and end date for a custom range.' })
      return
    }

    if (view !== 'availability' && view !== 'network-services') {
      setStatusMessage(null)
      setRunKey((k) => k + 1)
      return
    }

    setIsLoading(true)
    setStatusMessage(null)
    try {
      const qs = buildViewQuery(view, source)
      if (view === 'availability') {
        const data = await apiGet<Parameters<typeof fromHostAvailabilityResponse>[0]>(
          `/api/system/report/availability?${qs}`
        )
        if (sequence !== requestSequence.current) return
        setAvailability(fromHostAvailabilityResponse(data))
      } else {
        const data = await apiGet<Parameters<typeof fromNetworkServicesResponse>[0]>(
          `/api/system/report/network-services?${qs}`
        )
        if (sequence !== requestSequence.current) return
        setNetworkServices(fromNetworkServicesResponse(data))
      }
      setStale(false)
      if (showStatus) setStatusMessage({ type: 'success', text: 'Report generated successfully.' })
    } catch (err) {
      if (sequence !== requestSequence.current) return
      // Earlier rows stay on screen but are marked stale and cannot be exported.
      setStale(true)
      setStatusMessage({ type: 'error', text: errorMessage(err, 'Could not run report. Please try again.') })
    } finally {
      if (sequence === requestSequence.current) setIsLoading(false)
    }
  }

  const previousView = useRef(view)
  useEffect(() => {
    const viewChanged = previousView.current !== view
    previousView.current = view
    if (viewChanged && view !== 'availability' && view !== 'network-services') {
      requestSequence.current += 1
      setIsLoading(false)
      return
    }
    loadReport()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view])

  function runReport() {
    if (!customIncomplete(draft)) setApplied(draft)
    loadReport(true, draft)
  }

  // Opens Alerts for a Summary row or Histogram bucket, keeping the applied period and filters.
  function openAlerts(target: AlertDrilldown) {
    const next: Query = {
      ...applied,
      hostname: target.hostname ?? applied.hostname,
      service: target.hostname ? target.service ?? '' : applied.service,
      recurrence: target.recurrence ?? '',
    }
    setDraft(next)
    setApplied(next)
    setStatusMessage(null)
    setView('alerts')
    setRunKey((k) => k + 1)
  }

  const appliedQuery = buildViewQuery(view, applied)
  const periodOnlyQuery = periodQuery(applied).toString()
  const isAnalysis = view === 'alert-summary' || view === 'alert-histogram'
  const hostMeta = availability
    ? exportMeta(availability.period, {
        Filters: appliedQuery,
        Units: 'Durations are in seconds',
        Denominator: 'Uptime % = Up time / known host-state time (Up + Down + Unreachable); no recorded data is excluded',
      })
    : undefined
  const serviceMeta = networkServices
    ? exportMeta(networkServices.period, {
        Filters: appliedQuery,
        Units: 'Durations are in seconds',
        Denominator: 'Availability = OK time / recorded service-state time; scheduled maintenance included, no recorded data excluded',
        Warning: networkServices.current_status.available ? null : networkServices.current_status.notice,
      })
    : undefined

  // Host Availability cards describe the report period: known-time availability, problem time and coverage.
  const hostCards = useMemo(() => {
    if (!availability) return null
    const windowSeconds = Math.max(0, (Date.parse(availability.period.end) - Date.parse(availability.period.start)) / 1000)
    const known = availability.hosts.reduce((sum, h) => sum + h.knownSeconds, 0)
    const problem = availability.hosts.reduce((sum, h) => sum + h.downSeconds + h.unreachableSeconds, 0)
    const noData = Math.max(0, availability.hosts.length * windowSeconds - known)
    return { known, problem, noData }
  }, [availability])

  // Filters currently applied to this view, shown on the Filters button.
  const activeFilters = [
    SUPPORTS_HOST.includes(view) && applied.hostname,
    SUPPORTS_SERVICE.includes(view) && applied.hostname && applied.service,
    SUPPORTS_SCOPE.includes(view) && applied.scope !== 'both',
    SUPPORTS_STATE_TYPE.includes(view) && applied.stateType !== 'default',
    SUPPORTS_RECOVERIES.includes(view) && applied.includeRecoveries,
    view === 'notifications' && applied.contact,
  ].filter(Boolean).length

  const currentView = VIEW_TABS.find((t) => t.value === view)
  const description = currentView?.description ?? ''

  return (
    <main className="ml-55 flex-1">
      <div className="space-y-6 p-6">

        <PageHeader
          title="Reports"
          highlight={currentView?.label}
        />

        {/* Summary Cards */}
        {(view === 'availability' || view === 'network-services') && (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-4">
          {view === 'availability' ? (
            <>
              <SummaryStatCard
                title="Hosts"
                value={String(availability?.summary.total ?? 0)}
                subtitle="Objects in this report"
                icon={Activity}
                gradient="linear-gradient(135deg,#FFB100,#F59E0B)"
              />
              <SummaryStatCard
                title="Availability"
                value={availability?.summary.uptimePct != null ? `${availability.summary.uptimePct}%` : '—'}
                subtitle="Of known time, all hosts"
                icon={CheckCircle2}
                gradient="linear-gradient(135deg,#22C55E,#16A34A)"
              />
              <SummaryStatCard
                title="Problem time"
                value={hostCards ? formatDuration(hostCards.problem) : '—'}
                subtitle="Down + Unreachable (object-time)"
                icon={XCircle}
                gradient="linear-gradient(135deg,#EF4444,#DC2626)"
              />
              <SummaryStatCard
                title="No recorded data"
                value={hostCards ? formatDuration(hostCards.noData) : '—'}
                subtitle="Excluded from availability"
                icon={Activity}
                gradient="linear-gradient(135deg,#6B7280,#4B5563)"
              />
            </>
          ) : (
            <>
              <SummaryStatCard
                title="Total Services"
                value={String(networkServices?.summary.totalServices ?? 0)}
                subtitle={`${networkServices?.summary.totalInstances ?? 0} instances`}
                icon={Activity}
                gradient="linear-gradient(135deg,#FFB100,#F59E0B)"
              />
              <SummaryStatCard
                title="Current OK"
                value={String(networkServices?.summary.ok ?? 0)}
                subtitle="Healthy instances"
                icon={CheckCircle2}
                gradient="linear-gradient(135deg,#22C55E,#16A34A)"
              />
              <SummaryStatCard
                title="Current Warning / Critical"
                value={String((networkServices?.summary.warning ?? 0) + (networkServices?.summary.critical ?? 0))}
                subtitle="Needs attention"
                icon={XCircle}
                gradient="linear-gradient(135deg,#EF4444,#DC2626)"
              />
              <SummaryStatCard
                title="Availability"
                value={networkServices?.summary.uptimePct != null ? `${networkServices.summary.uptimePct}%` : '—'}
                subtitle="During recorded service time"
                icon={Activity}
                gradient="linear-gradient(135deg,#6B7280,#4B5563)"
              />
            </>
          )}
        </div>
        )}

        {view !== 'availability' && view !== 'network-services' && view !== 'alert-histogram' && extraCards.length > 0 && (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-4">
            {extraCards.map((card) => (
              <SummaryStatCard key={card.title} {...card} />
            ))}
          </div>
        )}

        {/* Report tabs */}
        <div role="tablist" aria-label="Report" className="flex flex-wrap gap-x-6 gap-y-2 border-b border-gray-200 dark:border-white/10">
          {VIEW_TABS.map((tab) => (
            <button key={tab.value} type="button" role="tab" aria-selected={view === tab.value} onClick={() => setView(tab.value)}
              className={`pb-3 text-sm transition ${view === tab.value ? 'border-b-2 border-gray-900 font-medium text-gray-900 dark:border-white dark:text-white' : 'text-gray-500 hover:text-gray-900 dark:text-white/60 dark:hover:text-white'}`}>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Controls: one row; the narrowing filters sit behind a Filters button */}
        <form
          className="space-y-3"
          onSubmit={(event) => { event.preventDefault(); if (!isLoading) runReport() }}
        >
          <div className="flex flex-wrap items-center justify-end gap-2">
            <select
              aria-label="Report period"
              value={draft.period}
              onChange={(e) => patch({ period: e.target.value as ReportPeriod })}
              className={FIELD}
            >
              {PERIOD_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-[var(--card)] text-[var(--text)]">{opt.label}</option>
              ))}
            </select>

            {draft.period === 'custom' && (
              <>
                <input type="date" aria-label="Report start date" value={draft.customStart}
                  onChange={(e) => patch({ customStart: e.target.value })} className={FIELD} />
                <input type="date" aria-label="Report end date" value={draft.customEnd}
                  onChange={(e) => patch({ customEnd: e.target.value })} className={FIELD} />
              </>
            )}

            <button
              type="button"
              aria-expanded={showFilters}
              onClick={() => setShowFilters((v) => !v)}
              className={`flex h-10 items-center gap-2 rounded-xl border px-3 text-sm ${showFilters || activeFilters > 0 ? 'border-[#ffb100] text-[var(--text)]' : 'border-[var(--border)] text-[var(--text-muted)]'}`}
            >
              <SlidersHorizontal className="h-4 w-4" />
              Filters{activeFilters > 0 ? ` (${activeFilters})` : ''}
            </button>

            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 rounded-lg bg-white border border-gray-300 px-4 py-2 font-medium text-gray-800 shadow-sm transition hover:bg-gray-50 hover:shadow dark:bg-[#171B20] dark:border-white/10 dark:text-white dark:hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
            >
              {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              {isLoading ? 'Running...' : 'Run Report'}
            </button>
          </div>

          {showFilters && (
            <div className="grid grid-cols-1 gap-3 rounded-2xl bg-white p-4 shadow-sm sm:grid-cols-2 lg:grid-cols-4 dark:bg-[#171B20]">
              <label className="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
                Host
                <input aria-label="Host scope" list="report-hosts" value={draft.hostname}
                  placeholder={SUPPORTS_HOST.includes(view) ? 'All hosts' : 'Not used by this report'}
                  disabled={!SUPPORTS_HOST.includes(view)}
                  onChange={(e) => patch({ hostname: e.target.value, ...(e.target.value ? {} : { service: '' }) })}
                  className={FIELD} />
                <datalist id="report-hosts">{hostOptions.map((h) => <option key={h} value={h} />)}</datalist>
              </label>
              <label className="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
                Service
                <input aria-label="Service scope" list="report-services" value={draft.service}
                  placeholder={SUPPORTS_SERVICE.includes(view) ? (draft.hostname ? 'All services' : 'Choose a host first') : 'Not used by this report'}
                  disabled={!SUPPORTS_SERVICE.includes(view) || !draft.hostname}
                  onChange={(e) => patch({ service: e.target.value })} className={FIELD} />
                <datalist id="report-services">{serviceOptions.map((s) => <option key={s} value={s} />)}</datalist>
              </label>
              {SUPPORTS_SCOPE.includes(view) && (
                <label className="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
                  Objects
                  <select aria-label="Event objects" value={draft.scope}
                    onChange={(e) => patch({ scope: e.target.value as EventScope })} className={FIELD}>
                    <option value="both">Host and service</option>
                    <option value="host">Host only</option>
                    <option value="service">Service only</option>
                  </select>
                </label>
              )}
              {SUPPORTS_STATE_TYPE.includes(view) && (
                <label className="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
                  State type
                  <select aria-label="State type" value={draft.stateType}
                    onChange={(e) => patch({ stateType: e.target.value as EventStateType })} className={FIELD}>
                    <option value="default">{isAnalysis ? 'Default (HARD)' : 'Default (all)'}</option>
                    <option value="hard">HARD</option>
                    <option value="soft">SOFT</option>
                    <option value="both">HARD and SOFT</option>
                  </select>
                </label>
              )}
              {view === 'notifications' && (
                <label className="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
                  Contact
                  <input aria-label="Notification contact" value={draft.contact}
                    onChange={(e) => patch({ contact: e.target.value })} className={FIELD} />
                </label>
              )}
              {view === 'alert-summary' && (
                <label className="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
                  Group by
                  <select aria-label="Summary grouping" value={draft.by}
                    onChange={(e) => patch({ by: e.target.value as 'host' | 'service' })} className={FIELD}>
                    <option value="service">Host and service</option>
                    <option value="host">Host</option>
                  </select>
                </label>
              )}
              {view === 'alert-histogram' && (
                <label className="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
                  Histogram
                  <select aria-label="Histogram breakdown" value={draft.breakdown}
                    onChange={(e) => patch({ breakdown: e.target.value as HistogramBreakdown })} className={FIELD}>
                    <option value="hour">Hour of day (15 min)</option>
                    <option value="weekday">Day of week</option>
                    <option value="day_of_month">Day of month</option>
                    <option value="month">Month</option>
                  </select>
                </label>
              )}
              {SUPPORTS_RECOVERIES.includes(view) && (
                <label className="flex items-center gap-2 self-end pb-2 text-sm text-[var(--text-muted)]">
                  <input type="checkbox" checked={draft.includeRecoveries}
                    onChange={(e) => patch({ includeRecoveries: e.target.checked })} />
                  Include recoveries (counted separately)
                </label>
              )}
              <div className="flex items-end sm:col-span-2 lg:col-span-4 lg:justify-end">
                <button type="button" onClick={clearFilters} disabled={!draftHasFilters}
                  className="text-sm text-[var(--text-muted)] underline disabled:cursor-not-allowed disabled:no-underline disabled:opacity-50">
                  Clear filters
                </button>
              </div>
            </div>
          )}
        </form>

        {hasUnappliedChanges && (
          <div role="status" className="text-right text-sm text-amber-600 dark:text-amber-400">
            Changes not applied. Run Report to use the new settings; the results below and their exports still use the last applied query.
          </div>
        )}

        {view === 'alerts' && applied.recurrence && (
          <div className="flex items-center justify-end gap-2 text-sm text-[var(--text-muted)]">
            <span>Showing one recurring bucket ({applied.recurrence.replace(':', ' #')}).</span>
            <button type="button" className="underline" onClick={() => { patch({ recurrence: '' }) }}>Clear</button>
          </div>
        )}

        {/* Status message */}
        {statusMessage && (
          <div
            role={statusMessage.type === 'error' ? 'alert' : 'status'}
            className={`flex items-center justify-between gap-2 rounded-lg px-4 py-2 text-sm ${
              statusMessage.type === 'success'
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}
          >
            <span className="flex items-center gap-2">
              {statusMessage.type === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
              {statusMessage.text}
            </span>
            {statusMessage.type === 'error' && (
              <button type="button" disabled={isLoading} onClick={() => loadReport(true)} className="underline">Retry</button>
            )}
          </div>
        )}

        {view === 'availability' ? (
          <>
            <HostAvailabilityReportTable
              hosts={availability?.hosts ?? []}
              isLoading={isLoading}
              stale={stale}
              meta={hostMeta}
              onDetails={(hostname) => setDetailTarget({ hostname, service: null })}
            />
            <ReportNotes description={description}>
              <p>Availability % = time Up ÷ known time (Up + Down + Unreachable). Time Nagios has no record of is shown as "No recorded data" and excluded. Durations are in seconds. Assumptions: HARD states, no assumed initial state, and state not assumed while Nagios was not running.</p>
            </ReportNotes>
          </>
        ) : view === 'network-services' ? (
          <>
            <NetworkServicesReportTable
              observedAt={networkServices?.current_status.observed_at}
              services={networkServices?.services ?? []}
              isLoading={isLoading}
              stale={stale}
              meta={serviceMeta}
              onDetails={(hostname, service) => setDetailTarget({ hostname, service })}
            />
            <ReportNotes description={description}>
              {networkServices && <ServiceReportContext period={networkServices.period} current={networkServices.current_status} durations={networkServices.summary} />}
            </ReportNotes>
          </>
        ) : view === 'alert-summary' ? (
          <AlertSummaryReport query={appliedQuery} runKey={runKey} onStatus={setStatusMessage} onOpenAlerts={openAlerts} description={description} onCards={setExtraCards} />
        ) : view === 'alert-histogram' ? (
          <AlertHistogramReport query={appliedQuery} runKey={runKey} onStatus={setStatusMessage} onOpenAlerts={openAlerts} description={description} />
        ) : (
          <ExtraReports
            view={view}
            query={appliedQuery}
            runKey={runKey}
            onStatus={setStatusMessage}
            onCards={setExtraCards}
            onOpenDetail={(hostname, service) => setDetailTarget({ hostname, service })}
            description={description}
          />
        )}

        {detailTarget && (
          <AvailabilityDetailDrawer
            hostname={detailTarget.hostname}
            service={detailTarget.service}
            query={periodOnlyQuery}
            onClose={() => setDetailTarget(null)}
          />
        )}

      </div>
    </main>
  )
}
