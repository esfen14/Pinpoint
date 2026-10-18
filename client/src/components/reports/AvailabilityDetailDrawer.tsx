import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { DrawerShell } from '../shared/DrawerShell'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { useSystemSettings } from '../../contexts/SystemSettingsContext'
import { useDialogFocus } from '../../hooks/useDialogFocus'
import { apiGet, errorMessage } from '../../lib/api'
import { formatDuration, formatPct, stateLabel, STATE_COLOR } from '../../lib/reportFormat'
import { formatServerDateTime } from '../../utils/formatDateTime'
import type { AvailabilityDetail } from '../../types/report'

type Props = {
  hostname: string
  service: string | null
  // The applied period query (period/start/end) the report was run with.
  query: string
  onClose: () => void
}

export function AvailabilityDetailDrawer({ hostname, service, query, onClose }: Props) {
  const { settings } = useSystemSettings()
  const { hasPermission } = useCurrentUser()
  const [detail, setDetail] = useState<AvailabilityDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  useDialogFocus(onClose)

  const load = useCallback(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    const params = new URLSearchParams(query)
    params.set('hostname', hostname)
    if (service) params.set('service', service)
    apiGet<AvailabilityDetail>(`/api/system/report/availability-detail?${params.toString()}`)
      .then((data) => { if (!cancelled) setDetail(data) })
      .catch((err) => { if (!cancelled) setError(errorMessage(err, 'Could not load the availability detail.')) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [hostname, service, query])

  useEffect(() => load(), [load])

  const when = (ts: number) =>
    formatServerDateTime(new Date(ts * 1000).toISOString(), settings.dateTimeFormat, settings.timeZone)
  const window = detail?.totals.window_seconds ?? 0
  const zone = detail?.period.time_zone
  const title = service ? `${hostname} / ${service}` : hostname

  return (
    <DrawerShell title={title} titleId="availability-detail-title" dialog dismissOnOverlay onClose={onClose}>
      {loading && <p role="status">Loading availability detail…</p>}

      {error && (
        <div role="alert" className="space-y-3">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <button type="button" onClick={() => load()} className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm">
            Retry
          </button>
        </div>
      )}

      {detail && (
        <>
          <section aria-label="State durations">
            <h3 className="mb-3 text-[17px] font-semibold">State durations</h3>
            <div
              role="img"
              aria-label={`State durations over ${formatDuration(window)}: ${detail.totals.states
                .map((s) => `${stateLabel(s.state)} ${formatDuration(s.seconds)}`).join(', ')}, no recorded data ${formatDuration(detail.totals.no_recorded_data_seconds)}`}
              className="flex h-4 w-full overflow-hidden rounded bg-gray-200 dark:bg-white/10"
            >
              {[...detail.totals.states.map((s) => ({ key: s.state, seconds: s.seconds })),
                { key: 'no_data', seconds: detail.totals.no_recorded_data_seconds }].map((part) => (
                window > 0 && part.seconds > 0
                  ? <div key={part.key} style={{ width: `${(100 * part.seconds) / window}%`, background: STATE_COLOR[part.key] }} />
                  : null
              ))}
            </div>
            <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[13px]">
              {[...detail.totals.states.map((s) => s.state), 'no_data'].map((key) => (
                <li key={key} className="flex items-center gap-1.5">
                  <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: STATE_COLOR[key] }} />
                  {stateLabel(key)}
                </li>
              ))}
            </ul>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-[var(--border)] text-[var(--text-muted)]">
                  <tr>
                    <th className="py-2 pr-3">State</th>
                    <th className="py-2 pr-3">Duration</th>
                    <th className="py-2 pr-3">% total time</th>
                    <th className="py-2 pr-3">% known time</th>
                    <th className="py-2 pr-3">Scheduled</th>
                    <th className="py-2">Unscheduled</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.totals.states.map((s) => (
                    <tr key={s.state} className="border-b border-[var(--border)]">
                      <td className="py-2 pr-3">{stateLabel(s.state)}</td>
                      <td className="py-2 pr-3">{formatDuration(s.seconds)}</td>
                      <td className="py-2 pr-3">{formatPct(s.pct_of_total)}</td>
                      <td className="py-2 pr-3">{formatPct(s.pct_of_known)}</td>
                      <td className="py-2 pr-3">{formatDuration(s.scheduled_seconds)}</td>
                      <td className="py-2">{formatDuration(s.unscheduled_seconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-[13px] text-[var(--text-muted)]">
              Scheduled time (maintenance) is a part of each state's duration, not extra time.
            </p>
          </section>

          <section aria-label="Coverage">
            <h3 className="mb-3 text-[17px] font-semibold">Coverage</h3>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <dt>Requested time</dt><dd>{formatDuration(detail.totals.window_seconds)}</dd>
              <dt>Known time</dt><dd>{formatDuration(detail.totals.known_seconds)}</dd>
              <dt>No recorded data</dt><dd>{formatDuration(detail.totals.no_recorded_data_seconds)}</dd>
              <dt>Nagios had no data</dt><dd>{formatDuration(detail.totals.no_data_seconds)}</dd>
              <dt>Nagios not running</dt><dd>{formatDuration(detail.totals.nagios_not_running_seconds)}</dd>
              <dt>Unaccounted</dt><dd>{formatDuration(detail.totals.unaccounted_seconds)}</dd>
            </dl>
          </section>

          <section aria-label="State timeline">
            <h3 className="mb-3 text-[17px] font-semibold">State timeline</h3>
            {!detail.complete && <p role="alert">{detail.notice}</p>}
            {detail.complete && !detail.intervals_available && (
              <div role="alert" className="space-y-2 text-amber-600 dark:text-amber-400">
                <p>{detail.notice}</p>
                {detail.reconciliation && Object.keys(detail.reconciliation.differences).length > 0 && (
                  <ul className="list-disc pl-5 text-[13px]">
                    {Object.entries(detail.reconciliation.differences).map(([state, delta]) => (
                      <li key={state}>
                        {stateLabel(state)}: the events give {formatDuration(Math.abs(delta))} {delta > 0 ? 'more' : 'less'} than Nagios's native total.
                      </li>
                    ))}
                  </ul>
                )}
                <p className="text-[13px]">
                  This usually means Nagios counted time with no archive event, for example a state carried over
                  from before a restart or time while Nagios was not running.
                </p>
              </div>
            )}
            {detail.intervals_available && (
              <>
                <div className="flex h-8 w-full overflow-hidden rounded border border-[var(--border)]" role="group" aria-label="State timeline segments">
                  {detail.intervals.map((i) => (
                    <button
                      key={`${i.start}-${i.state}`}
                      type="button"
                      title={`${stateLabel(i.state)}: ${when(i.start)} to ${when(i.end)} (${formatDuration(i.duration_seconds)})`}
                      aria-label={`${stateLabel(i.state)}, ${when(i.start)} to ${when(i.end)}, ${formatDuration(i.duration_seconds)}`}
                      style={{ width: `${(100 * i.duration_seconds) / Math.max(1, window)}%`, background: STATE_COLOR[i.state], minWidth: 2 }}
                      className="focus:outline focus:outline-2 focus:outline-offset-[-2px] focus:outline-[#ffb100]"
                    />
                  ))}
                </div>
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-[var(--border)] text-[var(--text-muted)]">
                      <tr>
                        <th className="py-2 pr-3">Start</th>
                        <th className="py-2 pr-3">End</th>
                        <th className="py-2 pr-3">Duration</th>
                        <th className="py-2 pr-3">State</th>
                        <th className="py-2">Information</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.intervals.map((i) => (
                        <tr key={`${i.start}-${i.state}`} className="border-b border-[var(--border)] align-top">
                          <td className="py-2 pr-3">
                            {when(i.start)}
                            {i.clipped_start && <span className="block text-[13px] text-[var(--text-muted)]">began before this period</span>}
                            {i.unknown_onset && <span className="block text-[13px] text-[var(--text-muted)]">onset unknown</span>}
                          </td>
                          <td className="py-2 pr-3">
                            {i.continuing ? <span>Period end: {when(i.end)}<span className="block text-[13px] text-[var(--text-muted)]">continuing</span></span> : when(i.end)}
                          </td>
                          <td className="py-2 pr-3">
                            {formatDuration(i.duration_seconds)}
                            {(i.clipped_start || i.continuing) && <span className="block text-[13px] text-[var(--text-muted)]">within period only</span>}
                          </td>
                          <td className="py-2 pr-3">{stateLabel(i.state)}</td>
                          <td className="py-2 break-words">{i.information}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-3 text-[13px] text-[var(--text-muted)]">
                  Intervals agree with Nagios's native durations (within {detail.reconciliation?.tolerance_seconds} s).
                  Durations are clipped to the report period, so they can be shorter than the full outage.
                </p>
              </>
            )}
          </section>

          <section aria-label="About this detail" className="space-y-1 text-[13px] text-[var(--text-muted)]">
            <p>
              Period: {when(Date.parse(detail.period.start) / 1000)} to {when(Date.parse(detail.period.end) / 1000)}
              {zone ? ` (reporting time zone ${zone.name}, UTC offset ${zone.utc_offset_seconds / 3600} h)` : ''}
            </p>
            <p>Source: {detail.source}. Generated {when(Date.parse(detail.generated_at) / 1000)}.</p>
            <p>
              Assumptions: HARD states only; no initial state is assumed, so time before the first recorded
              transition is no recorded data.
            </p>
          </section>

          {hasPermission('system.history') && (
            <section aria-label="Related history">
              <Link to="/history" className="text-[#ffb100] underline">
                Open History
              </Link>
              <p className="mt-1 text-[13px] text-[var(--text-muted)]">Filter by {hostname} there to investigate further.</p>
            </section>
          )}
        </>
      )}
    </DrawerShell>
  )
}
