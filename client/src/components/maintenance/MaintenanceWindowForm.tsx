import { useState, type FormEvent } from 'react'
import { DropdownSelect } from '../shared/DropdownSelect'
import { MAX_COMMENT_CHARS, formToInput, isoToInput, validateForm, type MaintenanceForm } from '../../utils/maintenanceTime'
import type { MaintenanceDevice, MaintenanceInput, MaintenanceRecurrence, MaintenanceWindow } from '../../types/maintenance'

type Props = {
  devices: MaintenanceDevice[]
  /** The window being edited, or null to create one. */
  window: MaintenanceWindow | null
  /** The Time Zone setting: times are typed and shown in it. */
  timeZone: string
  isSaving: boolean
  /** An error from the server for the last save. */
  serverError: string | null
  onSubmit: (input: MaintenanceInput) => void
  onClose: () => void
}

const fieldClass = 'w-full rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 py-2 text-sm text-[var(--text)]'
const labelClass = 'mb-1 block text-xs font-medium text-[var(--text-muted)]'

function initialForm(window: MaintenanceWindow | null, timeZone: string): MaintenanceForm {
  if (!window) return { deviceId: null, start: '', end: '', recurrence: 'none', until: '', comment: '' }
  return {
    deviceId: window.scope.deviceId,
    start: isoToInput(window.startAt, timeZone),
    end: isoToInput(window.endAt, timeZone),
    recurrence: window.recurrence,
    until: isoToInput(window.recurrenceUntil, timeZone),
    comment: window.comment,
  }
}

export function MaintenanceWindowForm({ devices, window, timeZone, isSaving, serverError, onSubmit, onClose }: Props) {
  const [form, setForm] = useState<MaintenanceForm>(() => initialForm(window, timeZone))
  const [problem, setProblem] = useState<string | null>(null)
  const repeats = form.recurrence !== 'none'

  function change<K extends keyof MaintenanceForm>(key: K, value: MaintenanceForm[K]) {
    setForm((current) => ({ ...current, [key]: value }))
    setProblem(null)
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    const message = validateForm(form, timeZone)
    if (message) {
      setProblem(message)
      return
    }
    onSubmit(formToInput(form, timeZone))
  }

  return (
    <form
      onSubmit={submit}
      aria-label={window ? 'Edit maintenance window' : 'New maintenance window'}
      className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-sm"
    >
      <h2 className="text-base font-semibold text-[var(--text)]">
        {window ? 'Edit maintenance window' : 'New maintenance window'}
      </h2>
      <p className="mt-1 text-sm text-[var(--text-muted)]">
        Times are in your display time zone ({timeZone}). Nagios is told shortly before the window starts and ends the
        downtime by itself.
      </p>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <span className={labelClass}>Devices</span>
          <DropdownSelect
            label="Devices"
            value={form.deviceId === null ? '' : String(form.deviceId)}
            options={[{ value: '', label: 'All monitored devices' }, ...devices.map((device) => ({ value: String(device.id), label: device.name }))]}
            onChange={(value) => change('deviceId', value === '' ? null : Number(value))}
          />
        </div>

        <div>
          <span className={labelClass}>Repeats</span>
          <DropdownSelect
            label="Repeats"
            value={form.recurrence}
            options={[
              { value: 'none', label: 'Does not repeat' },
              { value: 'daily', label: 'Every day' },
              { value: 'weekly', label: 'Every week' },
            ]}
            onChange={(value) => change('recurrence', value as MaintenanceRecurrence)}
          />
        </div>

        <div>
          <label htmlFor="mw-start" className={labelClass}>Starts</label>
          <input id="mw-start" type="datetime-local" className={fieldClass} value={form.start} onChange={(event) => change('start', event.target.value)} />
        </div>

        <div>
          <label htmlFor="mw-end" className={labelClass}>Ends</label>
          <input id="mw-end" type="datetime-local" className={fieldClass} value={form.end} onChange={(event) => change('end', event.target.value)} />
        </div>

        {repeats && (
          <div>
            <label htmlFor="mw-until" className={labelClass}>Stop repeating after (optional)</label>
            <input id="mw-until" type="datetime-local" className={fieldClass} value={form.until} onChange={(event) => change('until', event.target.value)} />
          </div>
        )}

        <div className={repeats ? '' : 'md:col-span-2'}>
          <label htmlFor="mw-comment" className={labelClass}>Reason</label>
          <input
            id="mw-comment"
            type="text"
            maxLength={MAX_COMMENT_CHARS}
            className={fieldClass}
            placeholder="For example: kernel updates on the web servers"
            value={form.comment}
            onChange={(event) => change('comment', event.target.value)}
          />
        </div>
      </div>

      {(problem || serverError) && (
        <p role="alert" className="mt-4 text-sm text-red-600 dark:text-red-400">{problem ?? serverError}</p>
      )}

      <div className="mt-5 flex justify-end gap-3">
        <button type="button" onClick={onClose} disabled={isSaving} className="rounded-xl border border-[var(--border)] px-4 py-2 text-sm text-[var(--text)] disabled:opacity-50">
          Close
        </button>
        <button type="submit" disabled={isSaving} className="rounded-lg bg-[#ffb100] px-4 py-2 text-sm font-semibold text-gray-900 hover:bg-[#f0a500] disabled:cursor-default disabled:opacity-50">
          {isSaving ? 'Saving…' : window ? 'Save changes' : 'Create window'}
        </button>
      </div>
    </form>
  )
}
