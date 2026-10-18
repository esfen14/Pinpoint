import type { CurrentServiceStatus, PeriodMeta, ServiceDurations } from '../../types/report'
import { useSystemSettings } from '../../contexts/SystemSettingsContext'
import { formatServerDateTime } from '../../utils/formatDateTime'

export function ServiceReportContext({ period, current, durations }: {
  period: PeriodMeta; current: CurrentServiceStatus; durations: ServiceDurations
}) {
  const { settings } = useSystemSettings()
  const display = (value: string | null) => formatServerDateTime(value, settings.dateTimeFormat, settings.timeZone)
  return <div className="space-y-2 rounded-xl border border-gray-200 p-4 text-sm text-gray-600 dark:border-white/10 dark:text-gray-300">
    <p>Availability during recorded time = OK ÷ (OK + Warning + Critical + Unknown) seconds.
      Scheduled maintenance is included. Missing coverage is excluded; — means no recorded state time.</p>
    <p>Period: {display(period.start)} to {display(period.end)} (end exclusive).
      Dates use the server’s time zone; times shown use your display preference.
      Reports stop at the last completed second to avoid assuming history from current status.</p>
    <p>Recorded time: {durations.known_seconds} seconds. No recorded data: {durations.no_recorded_data_seconds} seconds
      {' '}(Nagios no data: {durations.no_data_seconds}; engine not running: {durations.nagios_not_running_seconds};
      {' '}unaccounted time: {durations.unaccounted_seconds}). Totals sum service-instance time, so they may exceed the calendar window. Device aggregates describe service availability, not host uptime.</p>
    <p>Current status: {current.available ? (current.observed_at ? `observed ${display(current.observed_at)}` : 'no instances') : 'unavailable'}.
      Current states and check times describe now, including for past report periods. Missing results are unavailable; unchecked services are pending.</p>
    {current.notice && <p role="status">{current.notice}</p>}
    <p>Nagios archive retention and recorded checks limit coverage. Only currently configured objects returned by Nagios are counted;
      removed services may be absent. Unaccounted time has no confirmed state or cause.</p>
  </div>
}
