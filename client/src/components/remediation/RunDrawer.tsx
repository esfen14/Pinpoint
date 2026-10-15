import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { errorMessage } from '../../lib/api'
import { getRun } from '../../lib/remediationApi'
import { useSystemSettings } from '../../contexts/SystemSettingsContext'
import { formatServerDateTime } from '../../utils/formatDateTime'
import { OUTCOME_LABELS, type RemediationRunDetail } from '../../types/remediation'

type Props = {
  runId: number
  onClose: () => void
}

// Everything the log knows about one run, including its (redacted) output.
export function RunDrawer({ runId, onClose }: Props) {
  const { settings } = useSystemSettings()
  const [run, setRun] = useState<RemediationRunDetail | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getRun(runId)
      .then((data) => {
        if (!cancelled) setRun(data)
      })
      .catch((err) => {
        if (!cancelled) setLoadError(errorMessage(err, 'Unable to load this run.'))
      })
    return () => {
      cancelled = true
    }
  }, [runId])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const when = (value: string | null) =>
    value ? formatServerDateTime(value, settings.dateTimeFormat, settings.timeZone) : '—'

  const rows: [string, string][] = run
    ? [
        ['Action', run.actionName],
        ['Host', run.hostname],
        ['Service', run.service ?? '—'],
        ['State', `${run.state} (${run.stateType}, attempt ${run.attempt})`],
        ['Outcome', OUTCOME_LABELS[run.outcome] ?? run.outcome],
        ['Reason', run.reason ?? '—'],
        ['Received', when(run.receivedAt)],
        ['Started', when(run.startedAt)],
        ['Finished', when(run.finishedAt)],
      ]
    : []

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/50"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Run ${runId}`}
        className="h-full w-full max-w-xl overflow-y-auto bg-white shadow-xl dark:bg-[#171B20]"
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4 dark:border-white/10 dark:bg-[#171B20]">
          <h2 className="text-lg font-semibold text-[var(--text)]">Run {runId}</h2>
          <button type="button" aria-label="Close" onClick={onClose} className="rounded-lg p-2 hover:bg-[var(--hover)]">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 p-6">
          {loadError && (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-300">
              {loadError}
            </div>
          )}
          {!run && !loadError && <p className="text-sm text-[var(--text-muted)]">Loading run…</p>}
          {run && (
            <>
              <dl className="grid grid-cols-[8rem_1fr] gap-x-4 gap-y-2 text-sm">
                {rows.map(([label, value]) => (
                  <div key={label} className="contents">
                    <dt className="text-[var(--text-muted)]">{label}</dt>
                    <dd className="text-[var(--text)]">{value}</dd>
                  </div>
                ))}
              </dl>
              <div>
                <h3 className="mb-1 text-sm font-medium text-[var(--text)]">Output</h3>
                <pre className="whitespace-pre-wrap rounded-lg bg-[var(--hover)] p-3 text-sm text-[var(--text)]">
                  {run.output ?? 'No output.'}
                </pre>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
