import { useEffect, useState } from 'react'

import { errorMessage } from '../../lib/api'
import { getAddressEvidence } from '../../lib/deviceIdentityApi'
import { useDisplayTime } from '../../hooks/useDisplayTime'
import type { AddressEvidence } from '../../types/deviceIdentity'

type Props = { deviceId: number }

/**
 * Every IP address a device has been seen at, newest first, with when it was
 * first and last seen there. A device that moves .20 -> .25 -> .20 stays one
 * device; each move adds a row.
 */
export function DeviceAddressHistorySection({ deviceId }: Props) {
  const { formatDateTime } = useDisplayTime()
  const [addresses, setAddresses] = useState<AddressEvidence['addresses'] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [attempt, setAttempt] = useState(0)

  // The drawer remounts this section per device (key), so state starts empty.
  useEffect(() => {
    let cancelled = false
    getAddressEvidence(deviceId)
      .then((data) => { if (!cancelled) setAddresses(data.addresses) })
      .catch((err) => { if (!cancelled) setError(errorMessage(err, 'Unable to load IP address history.')) })
    return () => { cancelled = true }
  }, [deviceId, attempt])

  const retry = () => {
    setError(null)
    setAttempt((n) => n + 1)
  }

  return (
    <section>
      <h3 className="mb-2 text-[17px] font-semibold">IP address history</h3>
      {error && (
        <div className="flex items-center gap-3 text-[13px] text-red-600 dark:text-red-400">
          <span>{error}</span>
          <button type="button" className="underline" onClick={retry}>Retry</button>
        </div>
      )}
      {!addresses && !error && <p className="text-[var(--text-muted)]">Loading…</p>}
      {addresses && addresses.length === 0 && <p className="text-[var(--text-muted)]">No address history recorded.</p>}
      {addresses && addresses.length > 0 && (
        <table className="w-full text-left text-[13px]">
          <thead className="text-[var(--text-muted)]">
            <tr><th className="py-1 pr-3 font-medium">Address</th><th className="py-1 pr-3 font-medium">First seen</th><th className="py-1 font-medium">Last seen</th></tr>
          </thead>
          <tbody>
            {addresses.map((row) => (
              <tr key={row.id} className="border-t border-[var(--border)]">
                <td className="py-1 pr-3 font-medium">
                  {row.ip_address}
                  {row.current && <span className="ml-2 rounded bg-emerald-500/15 px-1.5 py-0.5 text-[11px] text-emerald-700 dark:text-emerald-400">Current</span>}
                </td>
                <td className="py-1 pr-3">{formatDateTime(row.first_seen_at)}</td>
                <td className="py-1">{formatDateTime(row.last_seen_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
