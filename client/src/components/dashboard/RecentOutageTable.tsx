import { useSystemSettings } from '../../contexts/SystemSettingsContext'
import { formatDateTime } from '../../utils/formatDateTime'
import type { AckFilter, AlertRow } from '../../types/dashboard'

type RecentOutageTableProps = {
  /** Alerts already narrowed by `filter`; Acknowledge all acts on exactly these. */
  alerts: AlertRow[]
  filter?: AckFilter
  onFilterChange?: (filter: AckFilter) => void
  isLoading: boolean
  onAcknowledge: (alert: AlertRow) => void
  onAcknowledgeAll?: () => void
  onUnacknowledge?: (alert: AlertRow) => void
}

const stateStyles: Record<string, string> = {
  DOWN: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  UNREACHABLE: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  CRITICAL: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  WARNING: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  UNKNOWN: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

export function RecentOutageTable({ alerts, filter = 'all', onFilterChange, isLoading, onAcknowledge, onAcknowledgeAll, onUnacknowledge }: RecentOutageTableProps) {
  const { settings } = useSystemSettings()
  const unacknowledgedCount = alerts.filter((alert) => !alert.ack).length

  return (
    <div className="rounded-2xl bg-[var(--card)] border border-[var(--border)] p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--text)]">Active Alerts</h2>
        <div className="flex items-center gap-2">
        {onFilterChange && (
          <select
            aria-label="Acknowledgement filter"
            value={filter}
            onChange={(e) => onFilterChange(e.target.value as AckFilter)}
            className="rounded-lg border border-[var(--border)] bg-[var(--card)] px-2 py-1.5 text-xs text-[var(--text)]"
          >
            <option value="all">Show all</option>
            <option value="hide-acknowledged">Hide acknowledged</option>
            <option value="only-acknowledged">Show only acknowledged</option>
          </select>
        )}
        {onAcknowledgeAll && unacknowledgedCount > 0 && (
          <button
            type="button"
            onClick={onAcknowledgeAll}
            className="rounded-lg bg-[#ffb100] px-3 py-1.5 text-xs font-semibold text-black hover:brightness-105"
          >
            Acknowledge all ({unacknowledgedCount})
          </button>
        )}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs text-[var(--text-muted)] border-b border-[var(--border)]">
              <th className="pb-3 pr-4 font-medium">Affected Device/Service</th>
              <th className="pb-3 pr-4 font-medium">Since</th>
              <th className="pb-3 pr-4 font-medium">Output</th>
              <th className="pb-3 pr-4 font-medium">Status</th>
              <th className="pb-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="py-8 text-center text-[var(--text-muted)]">Loading…</td></tr>
            ) : alerts.length === 0 ? (
              <tr><td colSpan={5} className="py-8 text-center text-[var(--text-muted)]">{filter === 'all' ? 'No active alerts' : 'No alerts match this filter'}</td></tr>
            ) : (
              alerts.map((alert) => (
                <tr key={`${alert.hostname}-${alert.serviceName ?? ''}`} className="border-t border-[var(--border)]">
                  <td className="py-3 pr-4 text-[var(--text)]">
                    {alert.hostname}{alert.serviceName ? ` / ${alert.serviceName}` : ''}
                  </td>
                  <td className="py-3 pr-4 text-[var(--text-muted)]">
                    {formatDateTime(new Date(alert.timestamp * 1000), settings.dateTimeFormat, settings.timeZone)}
                  </td>
                  <td className="py-3 pr-4 text-[var(--text-muted)] max-w-xs truncate">{alert.pluginOutput}</td>
                  <td className="py-3 pr-4">
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${stateStyles[alert.state] ?? stateStyles.UNKNOWN}`}>
                      {alert.state}{alert.inDowntime ? ' · Downtime' : ''}
                    </span>
                  </td>
                  <td className="py-3">
                    {alert.ack ? (
                      <span className="flex items-center gap-2 text-xs text-[var(--text-muted)]" title={alert.ack.comment}>
                        Acked by {alert.ack.acknowledgedBy}
                        {onUnacknowledge && (
                          <button
                            type="button"
                            onClick={() => onUnacknowledge(alert)}
                            className="underline hover:text-[var(--text)]"
                          >
                            Unacknowledge
                          </button>
                        )}
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => onAcknowledge(alert)}
                        className="rounded-lg bg-[#ffb100] px-3 py-1 text-xs font-semibold text-black hover:brightness-105"
                      >
                        Acknowledge
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
