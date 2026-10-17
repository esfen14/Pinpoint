import { useEffect, useState, type FormEvent } from 'react'
import { errorMessage } from '../../lib/api'
import { getRegisterCandidates, registerManualAgent } from '../../lib/ncpaDeploymentApi'
import type { RegisterCandidate, RegisterResult } from '../../types/ncpaDeployment'

// ``device`` is null when the dialog is opened from the page header: the user then picks the device.
type Props = { device: { id: number; hostname: string; ipAddress: string } | null; onClose: () => void; onRegistered: () => void }

const TOKEN_PATTERN = /^[0-9a-fA-F]{32}$/
const INPUT = 'w-full rounded-lg border border-gray-300 bg-transparent p-2 text-sm dark:border-white/20'

/** Register an NCPA agent the administrator installed themselves; the token is cleared after every call. */
export function RegisterAgentDialog({ device, onClose, onRegistered }: Props) {
  const [candidates, setCandidates] = useState<RegisterCandidate[]>([])
  const [loadingCandidates, setLoadingCandidates] = useState(device === null)
  const [pickedId, setPickedId] = useState('')
  const [token, setToken] = useState('')
  const [port, setPort] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<RegisterResult | null>(null)

  useEffect(() => {
    if (device !== null) return
    let cancelled = false
    getRegisterCandidates()
      .then((data) => { if (!cancelled) setCandidates(data) })
      .catch((err) => { if (!cancelled) setError(errorMessage(err, 'Unable to load devices.')) })
      .finally(() => { if (!cancelled) setLoadingCandidates(false) })
    return () => { cancelled = true }
  }, [device])

  const target = device ?? candidates.find((c) => String(c.id) === pickedId) ?? null

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    if (target === null) {
      setError('Choose a device.')
      return
    }
    const trimmed = token.trim()
    if (!TOKEN_PATTERN.test(trimmed)) {
      setError('The NCPA token must be 32 hexadecimal characters.')
      return
    }
    let portNumber: number | undefined
    if (port.trim()) {
      portNumber = Number(port)
      if (!Number.isInteger(portNumber) || portNumber < 1 || portNumber > 65535) {
        setError('The port must be a number between 1 and 65535.')
        return
      }
    }
    setSaving(true)
    try {
      setResult(await registerManualAgent(target.id, trimmed, portNumber))
      onRegistered()
    } catch (err) {
      setError(errorMessage(err, 'Unable to register the agent.'))
    } finally {
      setToken('')
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <form role="dialog" aria-modal="true" aria-labelledby="register-agent-title" onSubmit={submit}
        className="max-h-full w-full max-w-lg space-y-4 overflow-y-auto rounded-2xl bg-white p-6 text-gray-900 shadow-xl dark:bg-[#171B20] dark:text-white">
        <h2 id="register-agent-title" className="text-lg font-semibold">Register an agent I installed{target ? `: ${target.hostname}` : ''}</h2>
        <p className="text-sm">
          Use this when you installed NCPA on {target ? target.ipAddress : 'a device'} yourself. PinPoint checks that the agent answers with
          this token and reports a disk before it saves anything.
        </p>
        <details className="rounded-lg border border-gray-200 p-3 text-sm dark:border-white/10">
          <summary className="cursor-pointer font-medium">Installing NCPA on Windows</summary>
          <ol className="mt-2 list-decimal space-y-1 pl-5">
            <li>Download the NCPA Windows installer from the Nagios NCPA download page and run it on the server.</li>
            <li>Choose a token (32 hexadecimal characters) and set it as the agent&apos;s API token in the NCPA configuration.</li>
            <li>Restart the NCPA service so the token takes effect.</li>
            <li>Allow the NCPA port (5693 by default) through the Windows firewall from this PinPoint server.</li>
            <li>Enter the same token and port below.</li>
          </ol>
        </details>
        {result ? (
          <div role="status" className="space-y-1 text-sm text-emerald-700 dark:text-emerald-400">
            <p>Agent registered. Status: {result.agent_status}.</p>
            <p>Disks found: {result.disks.join(', ')}.</p>
            <p>{result.message}</p>
          </div>
        ) : (
          <>
            {device === null && (
              <div>
                <label htmlFor="register-device" className="mb-1 block text-sm">Device</label>
                <select id="register-device" value={pickedId} disabled={saving || loadingCandidates}
                  onChange={(e) => setPickedId(e.target.value)} className={INPUT}>
                  <option value="">{loadingCandidates ? 'Loading devices…' : candidates.length ? 'Choose a device' : 'No devices available'}</option>
                  {candidates.map((c) => (
                    <option key={c.id} value={c.id}>{c.hostname} ({c.ipAddress})</option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label htmlFor="register-token" className="mb-1 block text-sm">NCPA token</label>
              <input id="register-token" type="password" autoComplete="off" value={token} disabled={saving}
                onChange={(e) => setToken(e.target.value)} className={INPUT} />
            </div>
            <div>
              <label htmlFor="register-port" className="mb-1 block text-sm">Port (optional)</label>
              <input id="register-port" inputMode="numeric" placeholder="5693" value={port} disabled={saving}
                onChange={(e) => setPort(e.target.value)} className={INPUT} />
            </div>
          </>
        )}
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} disabled={saving} className="rounded-lg border px-4 py-2 text-sm">
            {result ? 'Done' : 'Cancel'}
          </button>
          {!result && (
            <button type="submit" disabled={saving} className="rounded-lg bg-[#ffb100] px-4 py-2 text-sm font-medium text-black disabled:opacity-50">
              {saving ? 'Registering…' : 'Register agent'}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
