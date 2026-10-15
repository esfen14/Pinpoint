import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { ApiError, errorMessage } from '../../lib/api'
import { getNotificationPolicy, saveNotificationPolicy } from '../../lib/notificationPolicyApi'
import type { HostNotificationOption, NotificationPolicy, QuietHourWindow, ServiceNotificationOption, Weekday } from '../../types/notificationPolicy'
import { DropdownSelect } from '../shared/DropdownSelect'
import { Layers, Server } from 'lucide-react'
import { SettingsToggle } from './SettingsToggle'
import { SettingsCard } from './SettingsCard'
import { SettingsActions } from './SettingsActions'

const weekdays: Weekday[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
const hostChoices: [HostNotificationOption, string, string][] = [['d', 'Down', 'bg-red-500'], ['u', 'Unreachable', 'bg-orange-500'], ['r', 'Recovery', 'bg-emerald-500'], ['f', 'Flapping', 'bg-violet-500'], ['s', 'Scheduled downtime', 'bg-sky-500']]
const serviceChoices: [ServiceNotificationOption, string, string][] = [['w', 'Warning', 'bg-amber-500'], ['u', 'Unknown', 'bg-gray-400'], ['c', 'Critical', 'bg-red-500'], ['r', 'Recovery', 'bg-emerald-500'], ['f', 'Flapping', 'bg-violet-500'], ['s', 'Scheduled downtime', 'bg-sky-500']]
const inputClass = 'h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-sm text-[var(--text)] outline-none transition duration-200 focus:border-[#ffb100]'
const labelClass = 'mb-2 block text-sm font-medium text-[var(--text)]'
const secondaryButton = 'rounded-xl border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] hover:bg-[var(--hover)]'
const timePattern = /^(?:[01]\d|2[0-3]):[0-5]\d$/

function validate(policy: NotificationPolicy): string | null {
  if (!Number.isInteger(policy.renotifyInterval) || policy.renotifyInterval < 0 || policy.renotifyInterval > 1440) {
    return 'Renotify interval must be from 0 to 1440 minutes.'
  }
  if (!policy.hostOptions.length || !policy.serviceOptions.length) return 'Select at least one host and service notification option.'
  const byDay = new Map<Weekday, QuietHourWindow[]>()
  for (const [index, window] of policy.quietHours.entries()) {
    if (!timePattern.test(window.start)) return `Quiet hours ${index + 1}: start must be HH:MM (24-hour time).`
    if (!timePattern.test(window.end)) return `Quiet hours ${index + 1}: end must be HH:MM (24-hour time).`
    if (window.start >= window.end) return `Quiet hours ${index + 1}: start must be before end. Split midnight crossings into two days.`
    byDay.set(window.weekday, [...(byDay.get(window.weekday) ?? []), window])
  }
  for (const periods of byDay.values()) {
    periods.sort((a, b) => a.start.localeCompare(b.start))
    if (periods.some((window, index) => index > 0 && window.start < periods[index - 1].end)) return 'Quiet hours on the same weekday must not overlap.'
  }
  return null
}

// One group of notification states: its own tinted panel so hosts and services read as two things.
function StatePanel({ icon: Icon, title, description, on, total, children }: { icon: typeof Server; title: string; description: string; on: number; total: number; children: ReactNode }) {
  return (
    <section aria-label={`${title} notification states`} className="rounded-2xl border border-[var(--border)] bg-[var(--card-alt)] p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Icon size={20} className="mt-0.5 shrink-0 text-[#ffb100]" />
          <div>
            <h3 className="text-sm font-semibold text-[var(--text)]">{title}</h3>
            <p className="mt-0.5 text-xs text-[var(--text-muted)]">{description}</p>
          </div>
        </div>
        <span className="shrink-0 rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs text-[var(--text-muted)]">{on} of {total} on</span>
      </div>
      <div className="mt-4 divide-y divide-[var(--border)] [&>div]:py-3 [&>div:first-child]:pt-0 [&>div:last-child]:pb-0">{children}</div>
    </section>
  )
}

export function NotificationPolicySettings() {
  const [saved, setSaved] = useState<NotificationPolicy | null>(null)
  const [form, setForm] = useState<NotificationPolicy | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [conflict, setConflict] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [savedMessage, setSavedMessage] = useState(false)

  const reload = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const policy = await getNotificationPolicy()
      setSaved(policy)
      setForm(structuredClone(policy))
      setSaveError(null)
      setConflict(false)
    } catch (err) {
      setLoadError(errorMessage(err, 'Unable to load notification policy.'))
    } finally {
      setLoading(false)
    }
  }, [])
  useEffect(() => { void reload() }, [reload])

  const update = (change: Partial<NotificationPolicy>) => {
    if (form) setForm({ ...form, ...change })
    setSaveError(null)
    setSavedMessage(false)
  }
  const save = async () => {
    if (!form) return
    const problem = validate(form)
    if (problem) { setSaveError(problem); return }
    setIsSaving(true)
    setSaveError(null)
    setConflict(false)
    try {
      const updated = await saveNotificationPolicy(form)
      setSaved(updated)
      setForm(structuredClone(updated))
      setSavedMessage(true)
    } catch (err) {
      setSaveError(errorMessage(err, 'Unable to save notification policy.'))
      setConflict(err instanceof ApiError && err.status === 409)
    } finally {
      setIsSaving(false)
    }
  }
  if (loading && !form) return <p role="status">Loading notification policy...</p>
  if (loadError) return <div role="alert">{loadError} <button type="button" onClick={() => void reload()}>Retry</button></div>
  if (!form || !saved) return <p role="status">Loading notification policy...</p>

  const updateWindow = (index: number, change: Partial<QuietHourWindow>) => update({ quietHours: form.quietHours.map((window, i) => i === index ? { ...window, ...change } : window) })
  const toggle = <T extends string,>(options: T[], item: T): T[] => options.includes(item) ? options.filter((value) => value !== item) : [...options, item]
  return <SettingsCard title="Notification policy" description="Choose when Nagios sends alert email. Quiet hours use the Nagios server's local time, not your display time zone.">
    <div className="space-y-6 text-sm text-[var(--text)]">
      <div>
        <h3 className={labelClass}>Quiet hours</h3>
        {form.quietHours.length === 0 && <p className="text-xs text-[var(--text-muted)]">No quiet hours — notifications are allowed 24x7.</p>}
        {form.quietHours.map((window, index) => <div key={index} className="mt-3 flex flex-wrap items-end gap-4">
          <div className="w-44"><span className={labelClass}>Weekday {index + 1}</span><DropdownSelect block label={`Weekday ${index + 1}`} value={window.weekday} options={weekdays.map((day) => ({ value: day, label: day[0].toUpperCase() + day.slice(1) }))} onChange={(value) => updateWindow(index, { weekday: value })} /></div>
          <div className="w-32"><label className={labelClass} htmlFor={`qh-start-${index}`}>Start {index + 1}</label><input id={`qh-start-${index}`} aria-label={`Start ${index + 1}`} className={inputClass} type="text" placeholder="HH:MM" value={window.start} onChange={(event) => updateWindow(index, { start: event.target.value })} /></div>
          <div className="w-32"><label className={labelClass} htmlFor={`qh-end-${index}`}>End {index + 1}</label><input id={`qh-end-${index}`} aria-label={`End ${index + 1}`} className={inputClass} type="text" placeholder="HH:MM" value={window.end} onChange={(event) => updateWindow(index, { end: event.target.value })} /></div>
          <button type="button" className={secondaryButton} aria-label={`Remove quiet hours ${index + 1}`} onClick={() => update({ quietHours: form.quietHours.filter((_, i) => i !== index) })}>Remove</button>
        </div>)}
        <button type="button" className={`mt-3 ${secondaryButton}`} onClick={() => update({ quietHours: [...form.quietHours, { weekday: 'monday', start: '', end: '' }] })}>Add quiet hours</button>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <StatePanel icon={Server} title="Hosts" description="Alerts about a whole device being reachable or not." total={hostChoices.length} on={form.hostOptions.length}>
          {hostChoices.map(([option, label, dot]) => <SettingsToggle key={option} label={label} dotClass={dot} enabled={form.hostOptions.includes(option)} onChange={() => update({ hostOptions: toggle(form.hostOptions, option) })} />)}
        </StatePanel>
        <StatePanel icon={Layers} title="Services" description="Alerts about one check on a device, such as HTTP, SSH or disk." total={serviceChoices.length} on={form.serviceOptions.length}>
          {serviceChoices.map(([option, label, dot]) => <SettingsToggle key={option} label={label} dotClass={dot} enabled={form.serviceOptions.includes(option)} onChange={() => update({ serviceOptions: toggle(form.serviceOptions, option) })} />)}
        </StatePanel>
      </div>
      <div className="w-48"><label className={labelClass} htmlFor="renotify-interval">Renotify interval (minutes)</label><input id="renotify-interval" aria-label="Renotify interval (minutes)" className={inputClass} type="number" value={form.renotifyInterval} onChange={(event) => update({ renotifyInterval: Number(event.target.value) })} /></div>
      <p className="text-xs text-[var(--text-muted)]">0 disables repeated notifications. An empty quiet-hours list permits email at all hours.</p>
    </div>
    {saveError && <p role="alert" className="mt-3 text-sm text-red-500">{saveError} {conflict && <button type="button" onClick={() => void reload()}>Reload policy</button>}</p>}
    {savedMessage && <p role="status" className="mt-3 text-sm text-emerald-500">Policy saved.</p>}
    {loading && <p role="status">Reloading policy...</p>}
    <button type="button" className="mt-3 text-sm underline" onClick={() => void reload()}>Reload policy</button>
    <SettingsActions hasChanges={JSON.stringify(form) !== JSON.stringify(saved)} onSave={save} onDiscard={() => { setForm(structuredClone(saved)); setSaveError(null) }} isSaving={isSaving} />
  </SettingsCard>
}
