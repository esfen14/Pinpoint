import { useState } from 'react'
import { errorMessage } from '../../lib/api'
import { cleanupDeployment } from '../../lib/ncpaDeploymentApi'
import type { CleanupResult, NcpaDevice } from '../../types/ncpaDeployment'

type Props = { device: NcpaDevice; onClose: () => void; onChanged: () => void }

export function CleanupDialog({ device, onClose, onChanged }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [removeAccount, setRemoveAccount] = useState(false)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<CleanupResult | null>(null)
  const [failure, setFailure] = useState<string | null>(null)

  const close = () => {
    if (busy) return
    setUsername('')
    setPassword('')
    onClose()
  }

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setFailure(null)
    setResult(null)
    try {
      const response = await cleanupDeployment(device.id, username, password, removeAccount)
      setResult(response)
      onChanged()
    } catch (err) {
      setFailure(errorMessage(err, 'Cleanup could not be completed.'))
    } finally {
      setUsername('')
      setPassword('')
      setBusy(false)
    }
  }

  return (
    <div role="dialog" aria-modal="true" aria-label={`Clean up ${device.hostname}`} className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg space-y-4 rounded-xl bg-white p-6 shadow-xl dark:bg-[#171B20] dark:text-white">
        <h2 className="text-lg font-semibold">Clean up failed deployment: {device.hostname}</h2>
        <p className="text-sm">Only the Pinpoint deployment key, sudo rule and helper will be removed from {device.ipAddress}. The saved SSH host key is rechecked before connecting. This does not uninstall NCPA.</p>
        <p className="text-xs">Trusted SSH key: SHA256:{device.fingerprint}</p>
        <form onSubmit={submit} className="space-y-3">
          <label className="block text-sm">SSH username
            <input aria-label="SSH username" autoComplete="off" required value={username} onChange={(event) => setUsername(event.target.value)} className="block w-full rounded border p-2 text-gray-900" />
          </label>
          <label className="block text-sm">SSH password
            <input aria-label="SSH password" type="password" autoComplete="new-password" required value={password} onChange={(event) => setPassword(event.target.value)} className="block w-full rounded border p-2 text-gray-900" />
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={removeAccount} onChange={(event) => setRemoveAccount(event.target.checked)} />
            Also remove the Pinpoint deployment account (only after the other steps succeed)
          </label>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={close} disabled={busy} className="rounded border px-3 py-2 text-sm">Close</button>
            <button type="submit" disabled={busy || !username || !password} className="rounded bg-[#ffb100] px-3 py-2 text-sm font-semibold text-gray-900 disabled:opacity-50">Run cleanup</button>
          </div>
        </form>
        {failure && <p role="alert" className="text-sm text-red-600">{failure}</p>}
        {result && <div role="status" className="text-sm">
          <p>{result.agent_status === 'Pending NCPA' ? 'Cleanup completed. Device is ready to deploy again.' : 'Cleanup incomplete; review the steps and retry.'}</p>
          <ul>{result.steps.map((step) => <li key={step.step}>{step.step}: {step.skipped ? 'skipped' : step.ok ? 'complete' : 'failed'}</li>)}</ul>
        </div>}
      </div>
    </div>
  )
}
