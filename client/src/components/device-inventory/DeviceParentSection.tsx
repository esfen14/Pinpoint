import { useEffect, useRef, useState } from 'react'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { errorMessage } from '../../lib/api'
import { getTopology, setDeviceParents } from '../../lib/topologyApi'
import { deviceLabel, parentIsEligible, type TopologyData } from '../../types/topology'

type Props = { deviceId: number; topology?: TopologyData; onChanged?: () => void }

export function DeviceParentSection({ deviceId, topology, onChanged }: Props) {
  const { hasPermission } = useCurrentUser()
  const [data, setData] = useState<TopologyData | null>(topology ?? null)
  const [selected, setSelected] = useState<number[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const dirty = useRef(false)
  const loadedDevice = useRef(deviceId)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    const request = topology ? Promise.resolve(topology) : getTopology()
    request.then(result => {
      if (cancelled) return
      if (!Array.isArray(result?.devices) || !Array.isArray(result?.edges)) throw new Error('Unable to load parent devices.')
      setData(result)
      if (!dirty.current || loadedDevice.current !== deviceId) {
        setSelected(result.devices.find(d => d.id === deviceId)?.parent_device_ids ?? [])
        dirty.current = false
        loadedDevice.current = deviceId
      }
    }).catch(err => { if (!cancelled) setError(errorMessage(err, 'Unable to load parent devices.')) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [deviceId, topology, reloadKey])

  const device = data?.devices.find(d => d.id === deviceId)
  const editable = hasPermission('system.hosts.edit') && device?.editable
  const choices = data?.devices.filter(d => d.id !== null && d.id !== deviceId &&
    (d.editable || selected.includes(d.id))) ?? []
  const selectedDevices = choices.filter(d => selected.includes(d.id!))
  const available = choices.filter(d => `${deviceLabel(d)} ${d.ip_address ?? ''}`.toLowerCase().includes(query.toLowerCase()))
  const warnings = selectedDevices.filter(d => !parentIsEligible(d))

  async function save() {
    setSaving(true)
    setError(null)
    setMessage(null)
    try {
      await setDeviceParents(deviceId, [...selected].sort((a, b) => a - b))
      dirty.current = false
      setMessage('Parent devices saved.')
      onChanged?.()
    } catch (err) {
      setError(errorMessage(err, 'Unable to save parent devices.'))
    } finally {
      setSaving(false)
    }
  }

  return <section className="space-y-3 rounded-xl border border-[var(--border)] p-4" aria-label="Parent devices">
    <h3 className="font-semibold">Parent devices</h3>
    <p className="text-sm text-[var(--text-muted)]">Choose the upstream devices used to reach this device. Connections are configured manually. No parents means Nagios treats it as directly reachable.</p>
    {loading && <p role="status">Loading parent devices…</p>}
    {error && <div role="alert">{error}{!data && <button type="button" onClick={() => setReloadKey(n => n + 1)}>Retry</button>}</div>}
    {!loading && data && <>
      <p className="text-sm">{selectedDevices.length ? selectedDevices.map(d => deviceLabel(d)).join(', ') : 'No parent devices configured.'}</p>
      {warnings.length > 0 && <p className="text-sm text-amber-600">{warnings.map(deviceLabel).join(', ')}: not used by Nagios while paused, retired, merged or address unknown.</p>}
      {editable ? <fieldset disabled={saving} className="space-y-3">
        <label className="block text-sm">Search parent devices<input type="search" value={query} onChange={e => setQuery(e.target.value)} className="mt-1 w-full rounded border border-[var(--border)] bg-transparent p-2" /></label>
        <div className="max-h-56 space-y-2 overflow-y-auto">
          {available.map(d => <label key={d.id} className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={selected.includes(d.id!)} onChange={e => { dirty.current = true; setMessage(null); setSelected(ids => e.target.checked ? [...ids, d.id!] : ids.filter(id => id !== d.id)) }} />
            <span>{deviceLabel(d)}{d.ip_address ? ` (${d.ip_address})` : ''} · {d.monitoring_state?.replaceAll('_', ' ')}{d.id === data.suggested_gateway_id && <span className="block text-xs">Suggested gateway — select only if appropriate</span>}</span>
          </label>)}
          {!available.length && <p>{choices.length ? 'No matching parent devices.' : 'No parent devices available.'}</p>}
        </div>
        <div className="flex gap-3"><button type="button" onClick={() => { dirty.current = true; setSelected([]); setMessage(null) }} className="rounded border px-3 py-2">Clear all</button><button type="button" onClick={save} className="rounded bg-blue-600 px-3 py-2 text-white">{saving ? 'Saving…' : 'Save parents'}</button></div>
      </fieldset> : <p className="text-sm text-[var(--text-muted)]">Parent relationships are read-only.</p>}
      {message && <p role="status">{message}</p>}
    </>}
  </section>
}
