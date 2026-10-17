import { useEffect, useState } from 'react'
import { useSystemSettings } from '../../contexts/SystemSettingsContext'
import { errorMessage } from '../../lib/api'
import { formatServerDateTime } from '../../utils/formatDateTime'
import type { RemediationHealth, RemediationSettings } from '../../types/remediation'

type Props = {
  // Null while loading or after a failed load; the message says which.
  health: RemediationHealth | null
  healthError: string | null
  settings: RemediationSettings | null
  settingsError: string | null
  isLoading: boolean
  canManage: boolean
  // True while the kill switch change is being saved, so it cannot be double-clicked.
  isSaving: boolean
  onToggleKillSwitch: () => void
  // Saves the repeat-recovery limits; rejects with the server's message when they are not valid.
  onSaveRepeatLimits: (repeatCount: number, repeatWindowHours: number) => Promise<void>
}

const numberClass =
  'h-9 w-24 rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-sm text-[var(--text)] outline-none transition focus:border-[#ffb100] disabled:opacity-60'

const alertClass =
  'rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-300'

function age(seconds: number | null): string {
  if (seconds === null) return 'none'
  if (seconds < 120) return `${seconds}s`
  return `${Math.round(seconds / 60)} min`
}

type StatProps = { label: string; value: string | number; testId: string; hint?: string }

function Stat({ label, value, testId, hint }: StatProps) {
  return (
    <div title={hint}>
      <dt className="text-xs text-[var(--text-muted)]">{label}</dt>
      <dd data-testid={testId} className="mt-1 text-sm font-semibold leading-snug text-[var(--text)] tabular-nums">
        {value}
      </dd>
    </div>
  )
}

// The health of the consumer that runs actions, and the kill switch that stops all of them.
// Shown above both tabs so a stalled consumer or a stopped system is never out of sight.
export function StatusPanel({
  health, healthError, settings, settingsError, isLoading, canManage, isSaving, onToggleKillSwitch, onSaveRepeatLimits,
}: Props) {
  const { settings: display } = useSystemSettings()
  const enabled = settings?.enabled ?? true
  const [repeatCount, setRepeatCount] = useState('')
  const [repeatWindow, setRepeatWindow] = useState('')
  const [repeatSaving, setRepeatSaving] = useState(false)
  const [repeatMessage, setRepeatMessage] = useState<{ text: string; ok: boolean } | null>(null)

  // Start from what is saved; typed values stay when a save fails.
  useEffect(() => {
    if (settings) {
      setRepeatCount(String(settings.repeatCount))
      setRepeatWindow(String(settings.repeatWindowHours))
    }
  }, [settings?.repeatCount, settings?.repeatWindowHours]) // eslint-disable-line react-hooks/exhaustive-deps

  const saveRepeat = async () => {
    setRepeatSaving(true)
    setRepeatMessage(null)
    try {
      await onSaveRepeatLimits(Number(repeatCount), Number(repeatWindow))
      setRepeatMessage({ text: 'Repeat limits saved.', ok: true })
    } catch (err) {
      setRepeatMessage({ text: errorMessage(err, 'Unable to save the repeat limits.'), ok: false })
    } finally {
      setRepeatSaving(false)
    }
  }

  return (
    <section aria-label="Automatic recovery status" className="space-y-3 rounded-xl border border-[var(--border)] p-4">
      {health?.stalled && (
        <div role="alert" className={alertClass}>
          <strong>Automatic recovery has stopped checking in.</strong> Failures are not being handled until it
          recovers. Last check-in:{' '}
          {health.lastTickAt ? formatServerDateTime(health.lastTickAt, display.dateTimeFormat, display.timeZone) : 'never'}.
          {health.lastError ? ` Last problem: ${health.lastError}` : ''}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text)]">Automatic recovery</h2>
          <p className="text-sm text-[var(--text-muted)]">
            {settings === null
              ? ' '
              : enabled
                ? 'On. Enabled actions run when a covered failure becomes a hard failure.'
                : 'Stopped. No action runs; each covered failure is logged as skipped.'}
          </p>
        </div>
        {settings !== null && (
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            aria-label="Automatic recovery"
            disabled={!canManage || isSaving}
            onClick={onToggleKillSwitch}
            className={`relative h-6 w-11 shrink-0 rounded-full transition disabled:cursor-not-allowed disabled:opacity-60 ${
              enabled ? 'bg-emerald-500' : 'bg-gray-300 dark:bg-white/20'
            }`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
                enabled ? 'left-[22px]' : 'left-0.5'
              }`}
            />
          </button>
        )}
      </div>
      {settingsError && <p role="alert" className="text-sm text-red-600">{settingsError}</p>}
      {settings !== null && !canManage && (
        <p className="text-sm text-[var(--text-muted)]">You need the remediation manage permission to change this.</p>
      )}

      {settings !== null && (
        <div className="space-y-2 border-t border-[var(--border)] pt-3">
          <h3 className="text-sm font-semibold text-[var(--text)]">Repeat recovery</h3>
          <p className="text-sm text-[var(--text-muted)]">
            When automatic recovery recovers the same service this many times inside the window, the operator is told once
            that the underlying fault persists.
          </p>
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label htmlFor="repeat-count" className="mb-1 block text-xs text-[var(--text-muted)]">Repeat count</label>
              <input
                id="repeat-count" type="number" className={numberClass} value={repeatCount} disabled={!canManage}
                onChange={(e) => setRepeatCount(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="repeat-window" className="mb-1 block text-xs text-[var(--text-muted)]">Repeat window (hours)</label>
              <input
                id="repeat-window" type="number" className={numberClass} value={repeatWindow} disabled={!canManage}
                onChange={(e) => setRepeatWindow(e.target.value)}
              />
            </div>
            {canManage && (
              <button
                type="button" onClick={saveRepeat} disabled={repeatSaving}
                className="rounded-xl bg-[#ffb100] px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
              >
                Save repeat limits
              </button>
            )}
          </div>
          {repeatMessage && (
            <p role={repeatMessage.ok ? 'status' : 'alert'} className={`text-sm ${repeatMessage.ok ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-600'}`}>
              {repeatMessage.text}
            </p>
          )}
        </div>
      )}

      {isLoading && <p className="text-sm text-[var(--text-muted)]">Checking status…</p>}
      {healthError && <p className="text-sm text-red-600">{healthError}</p>}

      {health && (
        <>
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <Stat
              label="Last check-in"
              testId="health-last-tick"
              value={health.lastTickAt ? formatServerDateTime(health.lastTickAt, display.dateTimeFormat, display.timeZone) : 'never'}
            />
            <Stat label="Events waiting" testId="health-backlog" value={health.backlog} hint={`Oldest: ${age(health.oldestSpoolAgeSeconds)}`} />
            <Stat label="Runs (24 h)" testId="health-runs" value={health.runsLast24h} hint="Actions that were started" />
            <Stat label="Limits hit (24 h)" testId="health-caps" value={health.capsHitLast24h} hint="Runs refused by the hourly limit" />
            <Stat label="Skipped (24 h)" testId="health-skipped" value={health.skippedLast24h} hint="Decisions that ran nothing" />
            <Stat label="Events dropped" testId="health-dropped" value={health.droppedTotal} hint="Discarded because too many were waiting" />
          </dl>
          {health.lastError && !health.stalled && (
            <p className="text-sm text-[var(--text-muted)]">
              Last problem: <span className="text-[var(--text)]">{health.lastError}</span>
            </p>
          )}
        </>
      )}
    </section>
  )
}
