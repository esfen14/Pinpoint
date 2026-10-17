import { useEffect, useState, type FormEvent } from 'react'
import { errorMessage } from '../../lib/api'
import { getRemoteRestart, saveRemoteRestart } from '../../lib/ncpaDeploymentApi'
import type { RemoteRestartSettings } from '../../types/ncpaDeployment'

type Props = { deviceId: number; hostname: string; onClose: () => void }

/** Edit the server's per-device switch/list; deployment writes the device's root-owned copy. */
export function RemoteRestartDialog({ deviceId, hostname, onClose }: Props) {
  const [settings, setSettings] = useState<RemoteRestartSettings | null>(null)
  const [enabled, setEnabled] = useState(false)
  const [services, setServices] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let cancelled = false
    getRemoteRestart(deviceId).then((data) => {
      if (cancelled) return
      setSettings(data)
      setEnabled(data.enabled)
      setServices(data.services.join('\n'))
    }).catch((err) => {
      if (!cancelled) setError(errorMessage(err, 'Unable to load restart settings.'))
    }).finally(() => {
      if (!cancelled) setLoading(false)
    })
    return () => { cancelled = true }
  }, [deviceId, retry])

  const save = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    setNotice(null)
    try {
      const data = await saveRemoteRestart(deviceId, {
        enabled, services: services.split('\n').map((name) => name.trim()).filter(Boolean),
      })
      setSettings(data)
      setEnabled(data.enabled)
      setServices(data.services.join('\n'))
      setNotice(data.redeploy_needed
        ? 'Saved. Clean up the existing deployment and redeploy NCPA to update the device’s service list.'
        : 'Saved. Changes to the service list require NCPA cleanup and redeployment before the device uses them.')
    } catch (err) {
      setError(errorMessage(err, 'Unable to save restart settings.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <form role="dialog" aria-modal="true" aria-labelledby="restart-settings-title" onSubmit={save}
        className="max-h-full w-full max-w-lg space-y-4 overflow-y-auto rounded-2xl bg-white p-6 text-gray-900 shadow-xl dark:bg-[#171B20] dark:text-white">
        <h2 id="restart-settings-title" className="text-lg font-semibold">Remote restart: {hostname}</h2>
        <p className="text-sm">Allow remediation actions to restart only the services listed for this device. Paused devices and Maintenance Mode block restarts.</p>
        <p className="text-sm">Devices deployed before this feature need NCPA cleanup and redeployment to install the restart helper. Changing this list also requires cleanup and redeployment with administrator credentials.</p>
        {loading && <p>Loading restart settings…</p>}
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        {notice && <p role="status" className="text-sm text-emerald-700 dark:text-emerald-400">{notice}</p>}
        {!loading && !settings && <button type="button" onClick={() => { setLoading(true); setError(null); setRetry((value) => value + 1) }}>Retry</button>}
        {!loading && settings && (
          <>
            {!settings.trusted && <p className="text-sm">Trust and deploy this device before enabling remote restart. You can prepare its service list now.</p>}
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={enabled} disabled={(!settings.trusted && !enabled) || saving} onChange={(event) => setEnabled(event.target.checked)} />
              Allow remote service restart
            </label>
            <label htmlFor="restart-services" className="block text-sm">Services allowed to restart</label>
            <textarea id="restart-services" rows={5} value={services} disabled={saving}
              onChange={(event) => setServices(event.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-transparent p-3 text-sm dark:border-white/20" />
            <p className="text-sm">One service name per line, such as apache2 or ncpa. Maximum 20 services. The device’s own list also has to allow the service.</p>
            {!services.trim() && <p className="text-sm">No services are allowed until you add them.</p>}
          </>
        )}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} disabled={saving} className="rounded-lg border px-4 py-2 text-sm">Close</button>
          {!loading && settings && <button type="submit" disabled={saving} className="rounded-lg bg-[#ffb100] px-4 py-2 text-sm font-medium text-black disabled:opacity-50">{saving ? 'Saving…' : 'Save settings'}</button>}
        </div>
      </form>
    </div>
  )
}
