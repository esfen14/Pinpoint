import { useEffect, useState } from 'react'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { apiGet, ApiError, errorMessage } from '../../lib/api'
import type { NagiosLogResponse } from '../../types/log'

export function NagiosLogPanel() {
  const { hasPermission } = useCurrentUser()
  const allowed = hasPermission('system.logs')
  const [refresh, setRefresh] = useState(0)
  const [data, setData] = useState<NagiosLogResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!allowed) return
    let cancelled = false
    setLoading(true)
    setError(null)
    setData(null)
    apiGet<NagiosLogResponse>('/api/system/log/nagios?lines=200')
      .then((result) => { if (!cancelled) setData(result) })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError && err.status === 403
          ? 'You do not have permission to view the Nagios log.'
          : errorMessage(err, 'Unable to load the Nagios log.'))
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [allowed, refresh])
  if (!allowed) return null
  return (
    <section aria-label="Nagios log" className="space-y-3 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4 text-[var(--text)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-semibold">Nagios log</h2>
        <button type="button" onClick={() => setRefresh((value) => value + 1)} disabled={loading}
          className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm disabled:opacity-50">Refresh Nagios log</button>
      </div>
      <p className="text-sm text-[var(--text-muted)]">Only the latest 200 lines within 64 KiB are shown, oldest first. Refresh to see new entries.</p>
      <p className="text-xs text-[var(--text-muted)]">State entries may contain hostnames, service names and addresses. Plugin output, commands and other messages are redacted to protect credentials. Nagios manages its own log rotation.</p>
      {loading ? <p role="status">Loading Nagios log…</p>
        : error ? <p role="alert" className="text-sm text-red-600">{error}</p>
        : !data?.available ? <p className="text-sm">Nagios log is unavailable. The server could not read the configured log file.</p>
        : data.lines.length === 0 ? <p className="text-sm">No Nagios log entries are available.</p>
        : <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap break-all rounded-lg bg-[var(--hover)] p-3 text-xs">{data.lines.join('\n')}</pre>}
    </section>
  )
}
