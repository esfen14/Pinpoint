import { useSystemSettings } from '../../contexts/SystemSettingsContext'
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
}

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
  health, healthError, settings, settingsError, isLoading, canManage, isSaving, onToggleKillSwitch,
}: Props) {
  const { settings: display } = useSystemSettings()
  const enabled = settings?.enabled ?? true

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
