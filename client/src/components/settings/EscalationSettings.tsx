import { useEffect, useState } from 'react'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { errorMessage } from '../../lib/api'
import { createEscalation, deleteEscalation, getEscalations, updateEscalation } from '../../lib/escalationApi'
import type { Escalation, EscalationInput, EscalationList } from '../../types/escalation'
import { SettingsCard } from './SettingsCard'

type Draft = { first: string; last: string; interval: string; group: string; host: string }
const inputClass = 'mt-1 block w-full rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 py-2 text-sm text-[var(--text)] disabled:opacity-50'
const buttonClass = 'rounded-xl border border-[var(--border)] px-3 py-2 text-sm disabled:opacity-50'
function emptyDraft(group = ''): Draft {
  return { first: '2', last: '5', interval: '10', group, host: '' }
}
function validate(draft: Draft): string | null {
  if (!/^\d+$/.test(draft.first) || Number(draft.first) < 1 || Number(draft.first) > 10000) return 'First notification must be an integer from 1 to 10000.'
  if (!/^\d+$/.test(draft.last) || Number(draft.last) < 1 || Number(draft.last) > 10000) return 'Last notification must be an integer from 1 to 10000.'
  if (Number(draft.first) > Number(draft.last)) return 'First notification must not exceed last notification.'
  if (!/^\d+$/.test(draft.interval) || Number(draft.interval) > 1440) return 'Interval must be an integer from 0 to 1440 minutes.'
  return null
}

export function EscalationSettings() {
  const { hasPermission } = useCurrentUser()
  return hasPermission('settings.system') ? <EscalationEditor /> : null
}

function EscalationEditor() {
  const [data, setData] = useState<EscalationList | null>(null)
  const [draft, setDraft] = useState<Draft>(emptyDraft())
  const [editing, setEditing] = useState<number | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getEscalations().then((result) => {
      if (!cancelled) {
        setData(result)
        setDraft(emptyDraft(result.groups.find((group) => group.member_count > 0)?.name))
      }
    }).catch((err) => { if (!cancelled) setError(errorMessage(err, 'Unable to load escalations.')) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const reload = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getEscalations()
      setData(result)
      return result
    } catch (err) {
      setError(errorMessage(err, 'Unable to load escalations.'))
      return null
    } finally { setLoading(false) }
  }
  const reset = (result = data) => {
    setEditing(null)
    setDraft(emptyDraft(result?.groups.find((group) => group.member_count > 0)?.name))
  }
  const startEdit = (row: Escalation) => {
    setEditing(row.id)
    setDraft({ first: String(row.first_notification), last: String(row.last_notification), interval: String(row.interval_minutes), group: row.contact_group, host: row.host_id === null ? '' : String(row.host_id) })
    setMessage(null)
    setError(null)
  }
  const save = async () => {
    const problem = validate(draft)
    if (problem) { setError(problem); return }
    if (!data?.groups.some((group) => group.name === draft.group && group.member_count > 0)) {
      setError('Choose a contact group with eligible members.'); return
    }
    setBusy(true)
    setError(null)
    setMessage(null)
    const input: EscalationInput = { first_notification: Number(draft.first), last_notification: Number(draft.last), interval_minutes: Number(draft.interval), contact_group: draft.group, host_id: draft.host === '' ? null : Number(draft.host) }
    try {
      if (editing === null) await createEscalation(input)
      else await updateEscalation(editing, input)
      setMessage('Escalation saved.')
      const result = await reload()
      // The mutation succeeded even if refreshing the list fails.
      reset(result)
    } catch (err) { setError(errorMessage(err, 'Unable to save escalation.')) }
    finally { setBusy(false) }
  }
  const confirmDelete = async () => {
    if (deleting === null) return
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      await deleteEscalation(deleting)
      if (editing === deleting) reset()
      setDeleting(null)
      setMessage('Escalation deleted.')
      await reload()
    } catch (err) { setError(errorMessage(err, 'Unable to delete escalation.')) }
    finally { setBusy(false) }
  }
  const change = (value: Partial<Draft>) => {
    setDraft({ ...draft, ...value })
    setError(null)
    setMessage(null)
  }
  const groupLabel = (name: string) => {
    if (name === 'system_users') return 'All eligible alert users'
    const hostId = Number(name.replace('pinpoint_host_', ''))
    const host = data?.hosts.find((item) => item.id === hostId)
    return host ? `Host recipients: ${host.name}` : `Host recipient group ${hostId}`
  }
  const eligible = data?.groups.some((group) => group.member_count > 0) ?? false
  const disabled = busy || loading
  return <div className="mt-6"><SettingsCard title="Escalations" description="Choose who receives repeated Nagios alerts after a notification count is reached.">
    <p className="mb-4 text-sm text-[var(--text-muted)]">Applies to the selected host and its services, or all Nagios hosts and services. Counts refer to notifications sent, not failed checks. During a range, Nagios uses the escalation group instead of the normal recipients. Create host recipient groups on the host detail page. Active users must have email alerts enabled. Quiet hours, acknowledgements and downtime still suppress alerts.</p>
    {loading && <p role="status">Loading escalations...</p>}
    {error && <p role="alert" className="mb-3 text-sm text-red-500">{error}</p>}
    {!data && !loading && <button type="button" className={buttonClass} onClick={() => void reload().then((result) => { if (result) reset(result) })}>Retry escalations</button>}
    {message && <p role="status" className="mb-3 text-sm text-emerald-500">{message}</p>}
    {data && <>
      <button type="button" className={buttonClass} disabled={disabled} onClick={() => void reload()}>Reload escalations</button>
      {data.items.length === 0 ? <p className="my-4 text-sm">No escalations defined.</p> : <div className="my-4 overflow-x-auto"><table className="w-full text-left text-sm">
        <thead><tr>{['Contact group', 'Scope', 'First notification', 'Last notification', 'Interval (minutes)', 'Status', 'Actions'].map((label) => <th key={label} className="p-2">{label}</th>)}</tr></thead>
        <tbody>{data.items.map((row) => <tr key={row.id} className="border-t border-[var(--border)]">
          <td className="p-2">{groupLabel(row.contact_group)}</td><td className="p-2">{row.host_id === null ? 'All hosts and services' : data.hosts.find((host) => host.id === row.host_id)?.name ?? `Unavailable host ${row.host_id}`}</td>
          <td className="p-2">{row.first_notification}</td><td className="p-2">{row.last_notification}</td><td className="p-2">{row.interval_minutes}</td>
          <td className="p-2">{row.active ? 'Active' : row.reason}</td>
          <td className="space-x-2 p-2"><button type="button" className={buttonClass} disabled={disabled} aria-label={`Edit escalation ${row.id}`} onClick={() => startEdit(row)}>Edit</button><button type="button" className={buttonClass} disabled={disabled} aria-label={`Delete escalation ${row.id}`} onClick={() => setDeleting(row.id)}>Delete</button></td>
        </tr>)}</tbody>
      </table></div>}
      {!eligible && <p className="my-4 text-sm">No recipient group has eligible members. Enable email alerts for an Active account, then reload the groups.</p>}
      <form className="mt-4 space-y-4" onSubmit={(event) => { event.preventDefault(); void save() }}>
        <fieldset disabled={disabled || !eligible} className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <legend className="mb-3 text-sm font-medium">{editing === null ? 'Add an escalation' : `Edit escalation ${editing}`}</legend>
          <label className="text-sm">Contact group<select aria-label="Contact group" className={inputClass} value={draft.group} onChange={(event) => change({ group: event.target.value })}>
            <option value="">Choose a group</option>
            {!data.groups.some((group) => group.name === draft.group) && draft.group && <option value={draft.group}>{draft.group} (unavailable)</option>}
            {data.groups.map((group) => <option key={group.name} value={group.name} disabled={group.member_count === 0}>{groupLabel(group.name)} ({group.member_count} eligible)</option>)}
          </select></label>
          <label className="text-sm">Scope<select aria-label="Scope" className={inputClass} value={draft.host} onChange={(event) => change({ host: event.target.value })}>
            <option value="">All hosts and services</option>
            {draft.host && !data.hosts.some((host) => String(host.id) === draft.host) && <option value={draft.host}>Unavailable host {draft.host}</option>}
            {data.hosts.map((host) => <option key={host.id} value={host.id}>{host.name}</option>)}
          </select></label>
          <label className="text-sm">First notification<input aria-label="First notification" className={inputClass} inputMode="numeric" value={draft.first} onChange={(event) => change({ first: event.target.value })} /></label>
          <label className="text-sm">Last notification<input aria-label="Last notification" className={inputClass} inputMode="numeric" value={draft.last} onChange={(event) => change({ last: event.target.value })} /></label>
          <label className="text-sm">Interval (minutes)<input aria-label="Interval (minutes)" className={inputClass} inputMode="numeric" value={draft.interval} onChange={(event) => change({ interval: event.target.value })} /></label>
        </fieldset>
        <p className="text-xs text-[var(--text-muted)]">First and last counts: 1–10000, first no greater than last. Interval: 0–1440 minutes; 0 sends once during the range. Empty groups are omitted from Nagios config until eligible members return.</p>
        <button type="submit" className={buttonClass} disabled={disabled || !eligible}>{busy ? 'Applying...' : editing === null ? 'Add escalation' : 'Save escalation'}</button>
        {editing !== null && <button type="button" className={`${buttonClass} ml-2`} disabled={disabled} onClick={() => reset()}>Cancel editing</button>}
      </form>
    </>}
    {deleting !== null && <div role="alertdialog" aria-label="Delete escalation" aria-describedby="delete-escalation-description" className="mt-4 rounded-xl border border-[var(--border)] p-4">
      <p id="delete-escalation-description" className="mb-3 text-sm">Delete escalation {deleting}? Its range will be removed from the Nagios configuration.</p>
      <button type="button" className={buttonClass} disabled={busy} onClick={() => void confirmDelete()}>Confirm deletion</button>
      <button type="button" className={`${buttonClass} ml-2`} disabled={busy} onClick={() => setDeleting(null)}>Cancel deletion</button>
    </div>}
  </SettingsCard></div>
}
