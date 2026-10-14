import { useEffect, useState } from 'react'

import { apiGet, errorMessage } from '../../lib/api'
import { useDisplayTime } from '../../hooks/useDisplayTime'

type FlapItem = {
  type: 'host' | 'service'
  hostname: string
  service: string | null
  snapshots_flagged: number
  first_flagged: string
  last_flagged: string
  currently_flapping: boolean
  current_state: string
}

type FlapResponse = {
  hours: number
  global_flap_detection_enabled: boolean | null
  items: FlapItem[]
}

// The windows GET /api/system/network-health/flapping accepts.
const WINDOWS = [
  { hours: 1, label: 'Last hour' },
  { hours: 6, label: 'Last 6 hours' },
  { hours: 24, label: 'Last 24 hours' },
  { hours: 168, label: 'Last 7 days' },
]

type Props = {
  hostname: string
  // The service name for a service view; null for the host itself.
  service: string | null
}

/**
 * How often this host or service was flagged as flapping. Nagios is sampled
 * about once a minute, so a very fast flap can be missed: the numbers are a
 * guide, not an exact count.
 */
export function FlapHistorySection({ hostname, service }: Props) {
  const { formatDateTime } = useDisplayTime()
  const [hours, setHours] = useState(24)
  const [data, setData] = useState<FlapResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setData(null)
    setError(null)
    apiGet<FlapResponse>(`/api/system/network-health/flapping?hours=${hours}`)
      .then((response) => {
        if (!cancelled) setData(response)
      })
      .catch((err) => {
        if (!cancelled) setError(errorMessage(err, 'Unable to load flap history.'))
      })
    return () => {
      cancelled = true
    }
  }, [hours])

  const items = Array.isArray(data?.items) ? data.items : []
  const entry = items.find((item) =>
    item.hostname === hostname && (service ? item.type === 'service' && item.service === service : item.type === 'host'))

  return (
    <section>
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="font-semibold">Flap history</h3>
        <select
          aria-label="Flap history window"
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="rounded-lg border border-[var(--border)] bg-[var(--input-bg)] px-2 py-1 text-xs text-[var(--text)]"
        >
          {WINDOWS.map((window) => (
            <option key={window.hours} value={window.hours}>{window.label}</option>
          ))}
        </select>
      </div>

      {data?.global_flap_detection_enabled === false && (
        <p className="mb-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-400">
          Flap detection is switched off in Nagios, so per-device flap settings have no effect and nothing new is flagged.
        </p>
      )}

      {error && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
      {!data && !error && <p className="text-[var(--text-muted)]">Loading…</p>}
      {data && !entry && (
        <p className="text-[var(--text-muted)]">Not flagged as flapping in this period.</p>
      )}
      {entry && (
        <div className="space-y-1">
          <p>
            Flagged as flapping in {entry.snapshots_flagged} {entry.snapshots_flagged === 1 ? 'check' : 'checks'}
            {entry.currently_flapping && <span className="ml-2 text-amber-600 dark:text-amber-400">Flapping now</span>}
          </p>
          <p className="text-xs text-[var(--text-muted)]">
            First {formatDateTime(entry.first_flagged)} · last {formatDateTime(entry.last_flagged)}
          </p>
        </div>
      )}
      <p className="mt-2 text-xs text-[var(--text-muted)]">
        Based on status checks about a minute apart, so very quick flaps can be missed.
      </p>
    </section>
  )
}
