import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useCurrentUser } from '../../contexts/CurrentUserContext'
import { useDisplayTime } from '../../hooks/useDisplayTime'
import { ApiError, errorMessage } from '../../lib/api'
import { getServiceRecovery, saveServiceRecovery } from '../../lib/remediationApi'
import {
  MAX_RESTARTS_PER_HOUR,
  MIN_RESTARTS_PER_HOUR,
  OUTCOME_LABELS,
  type ServiceRecovery,
} from '../../types/remediation'

type Props = {
  hostname: string
  service: string
}

function validLimit(text: string) {
  if (!/^\d+$/.test(text)) return null
  const value = Number(text)
  return value >= MIN_RESTARTS_PER_HOUR && value <= MAX_RESTARTS_PER_HOUR ? value : null
}

// The "Recover automatically" control of one service in the Device Inventory drawer
// (spec files/Frontend_Modules_and_Routes.md). One switch and one restart limit; the server
// picks the action and the service to restart, and the setting is the same row the Remediation
// page shows. Needs remediation.view to appear and remediation.manage to change.
export function ServiceRecoverySection({ hostname, service }: Props) {
  const { hasPermission } = useCurrentUser()
  const { formatDateTime } = useDisplayTime()
  const canView = hasPermission('remediation.view')
  const canManage = hasPermission('remediation.manage')

  const [data, setData] = useState<ServiceRecovery | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [enabled, setEnabled] = useState(false)
  const [limit, setLimit] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [stale, setStale] = useState(false)
  const [saved, setSaved] = useState(false)

  const show = useCallback((next: ServiceRecovery) => {
    setData(next)
    setEnabled(next.enabled)
    setLimit(String(next.maxRestartsPerHour))
  }, [])

  const load = useCallback(() => {
    let cancelled = false
    setData(null)
    setLoadError(null)
    setSaveError(null)
    setStale(false)
    setSaved(false)
    getServiceRecovery(hostname, service)
      .then((next) => {
        if (!cancelled) show(next)
      })
      .catch((err) => {
        if (cancelled) return
        setLoadError(
          err instanceof ApiError && err.status === 403
            ? 'You do not have permission to see this setting.'
            : errorMessage(err, 'Unable to load the recovery setting.'),
        )
      })
    return () => {
      cancelled = true
    }
  }, [hostname, service, show])

  useEffect(() => {
    if (!canView) return
    return load()
  }, [canView, load])

  if (!canView) return null

  const parsedLimit = validLimit(limit)
  const limitError =
    parsedLimit === null
      ? `Restarts per hour must be a whole number from ${MIN_RESTARTS_PER_HOUR} to ${MAX_RESTARTS_PER_HOUR}.`
      : null
  const dirty = data !== null && (enabled !== data.enabled || parsedLimit !== data.maxRestartsPerHour)
  const switchLocked = !canManage || isSaving || (data !== null && !data.canEnable && !data.enabled)

  async function save() {
    if (data === null || parsedLimit === null) return
    setIsSaving(true)
    setSaveError(null)
    setStale(false)
    setSaved(false)
    try {
      const next = await saveServiceRecovery(hostname, service, {
        enabled,
        maxRestartsPerHour: parsedLimit,
        version: data.version,
      })
      show(next)
      setSaved(true)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setStale(true)
        setSaveError('This setting was changed by someone else. Reload to see the current one.')
      } else if (err instanceof ApiError && err.status === 403) {
        setSaveError('You do not have permission to change this setting.')
      } else {
        setSaveError(errorMessage(err, 'Unable to save the recovery setting.'))
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section>
      <h3 className="mb-2 text-[17px] font-semibold">Recover automatically</h3>

      {loadError && (
        <div role="alert" className="space-y-2 text-[13px] text-red-600 dark:text-red-400">
          <p>{loadError}</p>
          <button
            type="button"
            onClick={load}
            className="rounded-lg border border-[var(--border)] px-3 py-1 text-[var(--text)] hover:bg-[var(--hover)]"
          >
            Try again
          </button>
        </div>
      )}

      {!loadError && data === null && (
        <p className="text-[13px] text-[var(--text-muted)]">Loading recovery setting…</p>
      )}

      {data && (
        <div className="space-y-3">
          <p className="text-[13px] text-[var(--text-muted)]">
            When this check stays failed, PinPoint restarts the service for you instead of waiting for someone to do it.
            It restarts at most the number of times you set per hour, pauses between restarts, and does nothing during
            Maintenance Mode or while automatic recovery is switched off on the Remediation page.
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <label className="flex items-center gap-2 text-[15px]">
              <button
                type="button"
                role="switch"
                aria-checked={enabled}
                aria-label="Recover automatically"
                disabled={switchLocked}
                onClick={() => {
                  setEnabled((value) => !value)
                  setSaved(false)
                }}
                className={`relative h-6 w-11 rounded-full transition disabled:cursor-not-allowed disabled:opacity-50 ${
                  enabled ? 'bg-[#ffb100]' : 'bg-gray-400/60'
                }`}
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${
                    enabled ? 'left-[22px]' : 'left-0.5'
                  }`}
                />
              </button>
              <span aria-hidden="true">{enabled ? 'On' : 'Off'}</span>
            </label>

            <label className="flex items-center gap-2 text-[13px] text-[var(--text-muted)]">
              Restarts per hour
              <input
                type="number"
                min={MIN_RESTARTS_PER_HOUR}
                max={MAX_RESTARTS_PER_HOUR}
                step={1}
                value={limit}
                disabled={!canManage || isSaving}
                onChange={(event) => {
                  setLimit(event.target.value)
                  setSaved(false)
                }}
                className="w-20 rounded-lg border border-[var(--border)] bg-[var(--input-bg)] px-2 py-1 text-[15px] text-[var(--text)] outline-none focus:border-[#ffb100] disabled:opacity-50"
              />
            </label>

            {canManage && (
              <button
                type="button"
                disabled={!dirty || limitError !== null || isSaving}
                onClick={save}
                className="rounded-lg bg-[#ffb100] px-3 py-1.5 text-[13px] font-semibold text-black disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSaving ? 'Saving…' : 'Save'}
              </button>
            )}
          </div>

          {limitError && <p className="text-[13px] text-red-600 dark:text-red-400">{limitError}</p>}

          {data.reason && <p className="text-[13px] text-[var(--text-muted)]">{data.reason}</p>}

          {!canManage && (
            <p className="text-[13px] text-[var(--text-muted)]">You can see this setting but not change it.</p>
          )}

          {enabled && dirty && data.unit && (
            <p
              role="note"
              className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[13px] text-amber-600 dark:text-amber-400"
            >
              Turning this on lets PinPoint restart {data.unit} on its own when this check fails, up to{' '}
              {parsedLimit ?? limit} times an hour.
            </p>
          )}

          {data.otherActions.length > 0 && (
            <p className="text-[13px] text-[var(--text-muted)]">
              Other automatic actions also cover this service: {data.otherActions.map((item) => item.name).join(', ')}.
            </p>
          )}

          {data.lastRun && (
            <p className="text-[13px] text-[var(--text-muted)]">
              {`Last result: ${OUTCOME_LABELS[data.lastRun.outcome]} · ${formatDateTime(data.lastRun.receivedAt)}`}{' '}
              <Link to="/remediation" className="text-[#ffb100] underline">
                View in Remediation
              </Link>
            </p>
          )}

          {saved && (
            <p role="status" className="text-[13px] text-emerald-600 dark:text-emerald-400">
              Saved.
            </p>
          )}

          {saveError && (
            <div role="alert" className="space-y-2 text-[13px] text-red-600 dark:text-red-400">
              <p>{saveError}</p>
              {stale && (
                <button
                  type="button"
                  onClick={load}
                  className="rounded-lg border border-[var(--border)] px-3 py-1 text-[var(--text)] hover:bg-[var(--hover)]"
                >
                  Reload
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
