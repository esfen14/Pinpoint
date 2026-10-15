import { useEffect, useState } from 'react'
import { apiGet, apiPut, errorMessage } from '../../lib/api'
import type { HostRecipients } from '../../types/hostRecipients'

export function DeviceRecipientsSection({ deviceId }: { deviceId: number }) {
  const [data, setData] = useState<HostRecipients | null>(null)
  const [selected, setSelected] = useState<number[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [retry, setRetry] = useState(0)
  const path = `/api/system/hosts/${deviceId}/recipients`

  useEffect(() => {
    let cancelled = false
    apiGet<HostRecipients>(path).then((result) => {
      if (!cancelled) {
        setData(result)
        setSelected(result.recipient_ids)
      }
    }).catch((err) => {
      if (!cancelled) setLoadError(errorMessage(err, 'Unable to load alert recipients.'))
    })
    return () => { cancelled = true }
  }, [path, retry])

  async function save() {
    setSaving(true)
    setSaveError(null)
    setSaved(false)
    try {
      const result = await apiPut<HostRecipients>(path, { recipient_ids: [...selected].sort((a, b) => a - b) })
      setData(result)
      setSelected(result.recipient_ids)
      setSaved(true)
    } catch (err) {
      setSaveError(errorMessage(err, 'Unable to save alert recipients.'))
    } finally {
      setSaving(false)
    }
  }

  const unchanged = data != null && selected.length === data.recipient_ids.length
    && selected.every((id) => data.recipient_ids.includes(id))
  const usingDefault = data != null && !data.users.some((user) => user.eligible && selected.includes(user.id))

  return (
    <section className="space-y-3">
      <h3 className="font-semibold">Email alert recipients</h3>
      <p className="text-xs text-[var(--text-muted)]">
        Choose who receives email alerts for this host and its services. Only active accounts with email alerts on receive them.
        Leave every box unchecked to use the default recipients.
      </p>
      {loadError ? (
        <div role="alert">
          <p className="text-red-600 dark:text-red-400">{loadError}</p>
          <button type="button" className="mt-2 rounded border border-[var(--border)] px-3 py-1"
            onClick={() => { setLoadError(null); setRetry((value) => value + 1) }}>Retry</button>
        </div>
      ) : !data ? <p className="text-[var(--text-muted)]">Loading recipients…</p> : (
        <>
          {!data.editable && <p className="text-[var(--text-muted)]">This device is retired or merged.</p>}
          {data.users.length === 0 && <p className="text-[var(--text-muted)]">No user accounts available.</p>}
          <div className="max-h-64 space-y-2 overflow-y-auto">
            {data.users.map((user) => (
              <label key={user.id} className="flex items-start gap-2 rounded border border-[var(--border)] p-2">
                <input type="checkbox" checked={selected.includes(user.id)} disabled={saving || !data.editable}
                  className="mt-1 accent-[#ffb100]"
                  onChange={(event) => {
                    setSelected((ids) => event.target.checked ? [...ids, user.id] : ids.filter((id) => id !== user.id))
                    setSaved(false)
                    setSaveError(null)
                  }} />
                <span className="min-w-0 break-words">
                  {user.name} <span className="text-[var(--text-muted)]">({user.email})</span>
                  {!user.eligible && <span className="block text-xs text-[var(--text-muted)]">Inactive or email alerts off; this account will not receive alerts.</span>}
                </span>
              </label>
            ))}
          </div>
          {usingDefault && <p className="text-xs text-amber-700 dark:text-amber-400">Using the default recipients: all active accounts with email alerts on.</p>}
          {data.editable && <button type="button" disabled={saving || unchanged}
            onClick={() => { void save() }}
            className="rounded-lg bg-[#ffb100] px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-50">
            {saving ? 'Saving…' : 'Save recipients'}
          </button>}
          {saveError && <p role="alert" className="text-red-600 dark:text-red-400">{saveError}</p>}
          {saved && <p role="status" className="text-emerald-700 dark:text-emerald-400">Alert recipients saved.</p>}
        </>
      )}
    </section>
  )
}
