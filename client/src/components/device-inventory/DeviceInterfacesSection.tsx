import { useCallback, useEffect, useState } from 'react'
import { Loader2, RefreshCw } from 'lucide-react'

import { errorMessage } from '../../lib/api'
import { getDeviceInterfaces, refreshDeviceInterfaces, setInterfaceMonitored } from '../../lib/bandwidthApi'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import type { DeviceInterface, DeviceInterfacesResponse } from '../../types/bandwidth'
import { formatLinkSpeed } from '../../utils/formatBandwidth'

type Props = {
  deviceId: number
  // The Nagios host name shown in messages.
  hostname: string
}

type Loaded = { deviceId: number; data: DeviceInterfacesResponse }

const STATUS_STYLES: Record<string, string> = {
  up: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
  down: 'bg-red-500/15 text-red-600 dark:text-red-400',
}

// The Interfaces section of the device drawer: the interfaces an SNMP device reports and a monitor on/off
// choice for each. A monitored interface gets an in and an out octet check in Nagios, which the Interface
// Bandwidth card on Network Health charts. Refresh reads the list from the device (system.hosts.edit);
// the server decides everything and the list is replaced by its answer after each action.
export function DeviceInterfacesSection({ deviceId, hostname }: Props) {
  const { hasPermission } = useCurrentUser()
  const canEdit = hasPermission('system.hosts.edit')

  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  const [busyIndex, setBusyIndex] = useState<number | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getDeviceInterfaces(deviceId)
      .then((data) => {
        if (cancelled) return
        setLoaded({ deviceId, data })
        setLoadError(null)
      })
      .catch((err) => {
        if (!cancelled) setLoadError(errorMessage(err, 'Unable to load the interfaces.'))
      })
    return () => {
      cancelled = true
    }
  }, [deviceId, reloadKey])

  const retry = useCallback(() => {
    setLoadError(null)
    setReloadKey((key) => key + 1)
  }, [])

  const data = loaded?.deviceId === deviceId ? loaded.data : null

  async function refresh() {
    setRefreshing(true)
    setActionError(null)
    setNotice(null)
    try {
      setLoaded({ deviceId, data: await refreshDeviceInterfaces(deviceId) })
    } catch (err) {
      setActionError(errorMessage(err, 'Unable to read the interfaces from the device.'))
    } finally {
      setRefreshing(false)
    }
  }

  async function toggle(row: DeviceInterface) {
    setBusyIndex(row.if_index)
    setActionError(null)
    setNotice(null)
    try {
      const result = await setInterfaceMonitored(deviceId, row.if_index, !row.monitored)
      setLoaded({ deviceId, data: result })
      if (result.config_ok === false) {
        setNotice(`The change was saved but Nagios was not updated: ${result.config_message}`)
      }
    } catch (err) {
      setActionError(errorMessage(err, 'Unable to change the interface.'))
    } finally {
      setBusyIndex(null)
    }
  }

  // Devices that do not answer SNMP have no interfaces to show: leave the drawer as it was.
  if (data && !data.snmp && data.interfaces.length === 0) return null

  const monitoredCount = data ? data.interfaces.filter((row) => row.monitored).length : 0

  return (
    <section>
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="text-[17px] font-semibold">Interfaces</h3>
        {data && canEdit && data.snmp && (
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={refreshing}
            className="flex items-center gap-1 rounded-lg border border-[var(--border)] px-2.5 py-1 text-[13px] font-medium hover:bg-[var(--hover)] disabled:opacity-50"
          >
            {refreshing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        )}
      </div>

      {!data && !loadError && (
        <p className="flex items-center text-[var(--text-muted)]">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading interfaces…
        </p>
      )}

      {loadError && (
        <div className="space-y-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-red-600 dark:text-red-400">
          <p>{loadError}</p>
          <button
            type="button"
            onClick={retry}
            className="rounded-lg border border-red-500/40 px-3 py-1 text-[13px] font-medium hover:bg-red-500/10"
          >
            Retry
          </button>
        </div>
      )}

      {data && data.interfaces.length === 0 && (
        <p className="text-[var(--text-muted)]">
          No interfaces read from {hostname} yet.{canEdit ? ' Choose Refresh to ask the device.' : ''}
        </p>
      )}

      {data && data.interfaces.length > 0 && (
        <p className="mb-2 text-[13px] text-[var(--text-muted)]">
          {monitoredCount} of {data.max_monitored} monitored. Each monitored interface adds an in and an out bandwidth check.
          {!canEdit && ' You can view interfaces but not change them.'}
        </p>
      )}

      {notice && (
        <p role="status" className="mb-2 rounded-lg bg-amber-500/10 px-3 py-2 text-[13px] text-amber-700 dark:text-amber-300">
          {notice}
        </p>
      )}
      {actionError && (
        <p role="alert" className="mb-2 rounded-lg bg-red-500/10 px-3 py-2 text-[13px] text-red-600 dark:text-red-400">
          {actionError}
        </p>
      )}

      {data && data.interfaces.length > 0 && (
        <ul className="space-y-2">
          {data.interfaces.map((row) => {
            const speed = formatLinkSpeed(row.speed_bps)
            const atLimit = !row.monitored && monitoredCount >= data.max_monitored
            return (
              <li key={row.if_index} className="flex items-center justify-between gap-3 rounded-lg border border-[var(--border)] px-3 py-2">
                <div className="min-w-0">
                  <p className="truncate font-medium">{row.name}</p>
                  <p className="flex flex-wrap items-center gap-x-2 text-[13px] text-[var(--text-muted)]">
                    <span>#{row.if_index}</span>
                    {speed && <span>{speed}</span>}
                    {row.oper_status && (
                      <span className={`rounded-full px-2 py-0.5 ${STATUS_STYLES[row.oper_status] ?? 'bg-gray-500/15'}`}>
                        {row.oper_status}
                      </span>
                    )}
                    {!row.present && <span>no longer reported by the device</span>}
                  </p>
                </div>
                <label className="flex shrink-0 items-center gap-2 text-[13px]">
                  {busyIndex === row.if_index && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  <input
                    type="checkbox"
                    checked={row.monitored}
                    aria-label={`Monitor ${row.name}`}
                    disabled={!canEdit || busyIndex !== null || (!row.monitored && (!row.present || atLimit))}
                    title={atLimit ? `At most ${data.max_monitored} interfaces can be monitored` : undefined}
                    onChange={() => void toggle(row)}
                  />
                  Monitor
                </label>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
