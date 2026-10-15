import { useEffect, useState } from 'react'
import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { useDisplayTime } from '../../hooks/useDisplayTime'
import { errorMessage } from '../../lib/api'
import { getIdentityReviews } from '../../lib/deviceIdentityApi'
import { IDENTITY_REVIEW_LABELS, identityReviews, deviceLabel, type IdentityReview, type MergeResult } from '../../types/deviceIdentity'
import { IdentityReviewDrawer } from './IdentityReviewDrawer'

type Props = { onMerged?: (result: MergeResult) => void; deviceId?: number; reloadKey?: number }
export function DeviceIdentityReviews({ onMerged, deviceId, reloadKey = 0 }: Props) {
  const { hasPermission } = useCurrentUser()
  const canReview = hasPermission('system.discover')
  const { formatDateTime } = useDisplayTime()
  const [items, setItems] = useState<IdentityReview[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [selected, setSelected] = useState<IdentityReview | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  useEffect(() => {
    if (!canReview) return
    let active = true
    setLoading(true); setError(null)
    getIdentityReviews().then(data => { if (active) setItems(identityReviews(data.items)) })
      .catch(err => { if (active) setError(errorMessage(err, 'Unable to load identity reviews.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [canReview, attempt, reloadKey])
  if (!canReview) return null
  const relevant = deviceId == null ? items : items.filter(item => item.devices.some(d => d.id === deviceId))
  if (deviceId != null && !loading && !error && !notice && relevant.length === 0) return null
  return <section aria-label={deviceId == null ? 'Device identity reviews' : 'Device identity notice'} className="space-y-3 rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 text-sm text-[var(--text)]">
    {deviceId == null && <h2 className="text-lg font-semibold">Needs Review ({loading || error ? '…' : items.length})</h2>}
    {notice && <p role="status">{notice}</p>}
    {loading && <p role="status">Loading identity reviews…</p>}
    {error && <div><p role="alert">{error}</p><button type="button" className="underline" onClick={() => setAttempt(a => a + 1)}>Retry</button></div>}
    {!loading && !error && (deviceId != null ? relevant.map(item => <div key={item.id}><p>This device needs identity review</p><button type="button" className="underline" onClick={() => setSelected(item)}>Review</button></div>) : relevant.length ? <div className="overflow-x-auto"><table className="w-full text-left"><thead><tr>{['Issue', 'Devices involved', 'Detected', 'Action'].map(label => <th className="p-2" key={label}>{label}</th>)}</tr></thead><tbody>{relevant.map(item => <tr className="border-t border-[var(--border)]" key={item.id}>
      <td className="p-2"><strong>{IDENTITY_REVIEW_LABELS[item.kind]}</strong><p>{item.message}</p></td>
      <td className="p-2">{item.devices.length ? item.devices.map(d => <p key={d.id}>{deviceLabel(d)}</p>) : 'Candidate device records unavailable'}</td>
      <td className="p-2">{formatDateTime(item.created_at)}</td><td className="p-2"><button type="button" className="rounded-lg border border-[var(--border)] px-3 py-2 hover:bg-[var(--hover)]" onClick={() => setSelected(item)}>Review</button></td>
    </tr>)}</tbody></table></div> : <p>No device identity issues need review.</p>)}
    {selected && <IdentityReviewDrawer key={selected.id} review={selected} onClose={() => setSelected(null)} onMerged={result => {
      setSelected(null)
      setNotice(result.config_ok === false ? `Merge saved. Nagios configuration warning: ${result.config_message}` : 'Merge saved.')
      setAttempt(a => a + 1)
      onMerged?.(result)
    }} />}
  </section>
}
