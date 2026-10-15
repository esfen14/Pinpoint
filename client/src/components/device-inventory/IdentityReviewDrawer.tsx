import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { useDisplayTime } from '../../hooks/useDisplayTime'
import { errorMessage } from '../../lib/api'
import { getAddressEvidence, getIdentityEvidence, lookupIdentityDevices, mergeIdentityDevices } from '../../lib/deviceIdentityApi'
import { deviceLabel, type AddressEvidence, type DeviceSummary, type IdentityEvidence, type IdentityReview, type MergeResult } from '../../types/deviceIdentity'

const button = 'rounded-lg border border-[var(--border)] px-3 py-2 text-sm hover:bg-[var(--hover)] disabled:opacity-50'
const input = 'w-full rounded-lg border border-[var(--border)] bg-[var(--input-bg)] p-2 text-[var(--text)]'

// Each modal owns keyboard focus and restores it to its opener on dismissal.
function FocusDialog({ title, onClose, children, busy = false }: { title: string; onClose: () => void; children: ReactNode; busy?: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null
    const dialog = ref.current
    dialog?.focus()
    return () => { if (opener?.isConnected) opener.focus() }
  }, [title])
  return <div className="fixed inset-0 z-[70] flex justify-end bg-black/60 p-2 sm:p-4">
    <div ref={ref} role="dialog" aria-modal="true" aria-label={title} tabIndex={-1}
      className="h-full w-full max-w-5xl space-y-4 overflow-y-auto rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 text-[var(--text)] shadow-xl"
      onKeyDown={event => {
        if (event.key === 'Escape') { event.stopPropagation(); if (!busy) onClose() }
        if (event.key !== 'Tab') return
        const nodes = Array.from(ref.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),[tabindex="0"]') ?? [])
        const first = nodes[0], last = nodes[nodes.length - 1]
        if (!first) { event.preventDefault(); return }
        if (event.shiftKey && (document.activeElement === first || document.activeElement === ref.current)) { event.preventDefault(); last.focus() }
        else if (!event.shiftKey && (document.activeElement === last || document.activeElement === ref.current)) { event.preventDefault(); first.focus() }
      }}>
      <div className="flex items-center justify-between gap-4"><h2 className="text-lg font-semibold">{title}</h2><button className={button} disabled={busy} onClick={onClose}>Close</button></div>
      {children}
    </div>
  </div>
}

function CandidateEvidence({ device, canRead }: { device: DeviceSummary; canRead: boolean }) {
  const { formatDateTime } = useDisplayTime()
  const [evidence, setEvidence] = useState<IdentityEvidence | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [addresses, setAddresses] = useState<AddressEvidence | null>(null)
  const [addressError, setAddressError] = useState<string | null>(null)
  const [loadingAddresses, setLoadingAddresses] = useState(false)
  useEffect(() => {
    if (!canRead) return
    let active = true
    getIdentityEvidence(device.id).then(data => { if (active) { setEvidence(data); setError(null) } })
      .catch(err => { if (active) setError(errorMessage(err)) })
    return () => { active = false }
  }, [device.id, canRead, attempt])
  async function loadAddresses() {
    setLoadingAddresses(true); setAddressError(null)
    try { setAddresses(await getAddressEvidence(device.id)) } catch (err) { setAddressError(errorMessage(err)) }
    finally { setLoadingAddresses(false) }
  }
  const current = evidence?.device ?? device
  return <article className="min-w-0 space-y-2 rounded-lg border border-[var(--border)] p-3 break-words">
    <h3 className="font-semibold">{current.display_name || 'Display name unavailable'}</h3>
    <dl className="space-y-1 text-sm">
      <div><dt>Stable device ID</dt><dd>{current.id}</dd></div>
      <div><dt>Nagios host name</dt><dd>{current.nagios_host_name || 'Unavailable'}</dd></div>
      <div><dt>Current IP</dt><dd>{current.ip_address || 'Unavailable'}</dd></div>
      <div><dt>Monitoring state</dt><dd>{current.monitoring_state.replaceAll('_', ' ')}</dd></div>
    </dl>
    {!canRead ? <p>system.hosts permission is required to view identity and address evidence.</p> : <>
      {!evidence && !error && <p role="status">Loading identity evidence…</p>}
      {error && <div><p role="alert">{error}</p><button className={button} onClick={() => setAttempt(a => a + 1)}>Retry evidence</button></div>}
      {evidence && <><p>Identity confidence: <strong>{evidence.confidence || 'Unavailable'}</strong></p>
        {evidence.identifiers.length ? <ul>{evidence.identifiers.map(row => <li key={row.id}>{row.kind.replaceAll('_', ' ')}: {row.value} ({row.strong ? 'strong' : 'weak'} evidence)</li>)}</ul> : <p>No identity identifiers available.</p>}
        {evidence.recommendation && <p>{evidence.recommendation}</p>}
      </>}
      <h4 className="font-medium">Address history</h4>
      {!addresses && <button className={button} disabled={loadingAddresses} onClick={() => void loadAddresses()}>{loadingAddresses ? 'Loading addresses…' : addressError ? 'Retry address history' : 'Load address history'}</button>}
      {addressError && <p role="alert">{addressError}</p>}
      {addresses && (addresses.addresses.length ? <ul>{addresses.addresses.map(row => <li key={row.id}>{row.ip_address} · {row.current ? 'Current' : 'Previous'} · {formatDateTime(row.first_seen_at)} – {formatDateTime(row.closed_at || row.last_seen_at)}</li>)}</ul> : <p>No address history available.</p>)}
    </>}
  </article>
}

export function IdentityReviewDrawer({ review, onClose, onMerged }: { review: IdentityReview; onClose: () => void; onMerged: (result: MergeResult) => void }) {
  const { hasPermission } = useCurrentUser()
  const canRead = hasPermission('system.hosts')
  const canMerge = canRead && hasPermission('system.hosts.edit')
  const [devices, setDevices] = useState(review.devices)
  const [targetId, setTargetId] = useState('')
  const [sourceId, setSourceId] = useState('')
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<DeviceSummary[]>([])
  const [searching, setSearching] = useState(false)
  const [searched, setSearched] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [confirming, setConfirming] = useState(false)
  const [saving, setSaving] = useState(false)
  const submitting = useRef(false)
  const [error, setError] = useState<string | null>(null)
  const source = devices.find(d => String(d.id) === sourceId)
  const target = devices.find(d => String(d.id) === targetId)
  const valid = canMerge && source && target && source.id !== target.id && source.state !== 'MERGED' && !['RETIRED', 'MERGED'].includes(target.state)
  async function findDevices() {
    setSearching(true); setSearchError(null)
    try { const data = await lookupIdentityDevices(search.trim()); setResults(data.items); setHasMore(data.has_more); setSearched(true) }
    catch (err) { setSearchError(errorMessage(err)) }
    finally { setSearching(false) }
  }
  async function save() {
    if (!valid || submitting.current) return
    submitting.current = true; setSaving(true); setError(null)
    let result: MergeResult
    try { result = await mergeIdentityDevices(source.id, target.id) }
    catch (err) { setError(errorMessage(err)); setConfirming(false); setSaving(false); submitting.current = false; return }
    // A committed merge stays a success even when refreshing the surrounding page fails.
    onMerged(result)
  }
  if (confirming && source && target) return <FocusDialog title="Confirm device merge" busy={saving} onClose={() => setConfirming(false)}>
    <p>Device record to keep: {deviceLabel(target)}</p>
    <p>Duplicate record to merge: {deviceLabel(source)}</p>
    <p>The target survives and retains its current address: {target.ip_address || 'Unavailable'}.</p>
    <p>The source becomes Merged and leaves monitoring.</p>
    <p>Target records take precedence where settings conflict.</p>
    <p>Historical monitoring snapshots remain under their original host names; they are not transferred.</p>
    <p>No undo action is provided.</p>
    <div className="flex gap-3"><button className={button} disabled={saving} onClick={() => setConfirming(false)}>Cancel</button><button className={button} disabled={saving} onClick={() => void save()}>{saving ? 'Saving…' : 'Merge duplicate'}</button></div>
  </FocusDialog>
  return <FocusDialog title="Review device identity" onClose={onClose}>
    <p>{review.message}</p>
    <p>Merge only after verifying that both records represent the same physical device. Similar names or matching IPs are not proof of identity. Keep the record with the intended monitoring settings and current address.</p>
    {devices.length === 0 && <p>No candidate device records available. Search discovered devices to compare records.</p>}
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{devices.map(device => <CandidateEvidence key={device.id} device={device} canRead={canRead} />)}</div>
    {canMerge && <section className="space-y-3" aria-label="Merge choices">
      <form className="space-y-2" onSubmit={e => { e.preventDefault(); void findDevices() }}>
        <label className="block">Search discovered devices<input className={input} value={search} maxLength={100} onChange={e => setSearch(e.target.value)} placeholder="Name, IP address or device ID" /></label>
        <button className={button} disabled={searching}>{searching ? 'Searching…' : 'Search'}</button>
      </form>
      {searchError && <p role="alert">{searchError} Try Search again.</p>}
      {searched && !results.length && <p>No discovered devices match.</p>}
      {hasMore && <p>Showing the first 20 matches. Refine your search by name, IP address or device ID.</p>}
      <ul>{results.map(device => <li key={device.id}><button className={button} disabled={devices.some(d => d.id === device.id)} onClick={() => setDevices(ds => [...ds, device])}>Add {device.display_name || device.nagios_host_name} · {deviceLabel(device)}</button></li>)}</ul>
      <label className="block">Device record to keep<select className={input} value={targetId} onChange={e => { setTargetId(e.target.value); setError(null) }}><option value="">Choose surviving target</option>{devices.filter(d => !['RETIRED', 'MERGED'].includes(d.state)).map(d => <option key={d.id} value={d.id}>{deviceLabel(d)}</option>)}</select></label>
      <label className="block">Duplicate record to merge<select className={input} value={sourceId} onChange={e => { setSourceId(e.target.value); setError(null) }}><option value="">Choose duplicate source</option>{devices.filter(d => d.state !== 'MERGED').map(d => <option key={d.id} value={d.id}>{deviceLabel(d)}</option>)}</select></label>
      {sourceId && sourceId === targetId && <p role="alert">Choose two distinct records.</p>}
      {error && <p role="alert">{error}</p>}
      <button className={button} disabled={!valid} onClick={() => setConfirming(true)}>Review merge</button>
    </section>}
  </FocusDialog>
}
