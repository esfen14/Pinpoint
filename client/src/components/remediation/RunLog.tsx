import { useEffect, useState } from 'react'
import { Eye } from 'lucide-react'
import { errorMessage } from '../../lib/api'
import { listRuns } from '../../lib/remediationApi'
import { useSystemSettings } from '../../contexts/SystemSettingsContext'
import { formatServerDateTime } from '../../utils/formatDateTime'
import { Pagination } from '../shared/Pagination'
import {
  OUTCOME_LABELS,
  notifyLabel,
  type RemediationAction,
  type RemediationOutcome,
  type RemediationRun,
} from '../../types/remediation'
import { RunDrawer } from './RunDrawer'

const PER_PAGE = 10

type Props = {
  // For the Action filter.
  actions: RemediationAction[]
  // A run to open straight away (from a link on a service row).
  initialRunId?: number | null
}

const filterClass =
  'h-10 rounded-xl border border-[var(--border)] bg-[var(--input-bg)] px-3 text-sm text-[var(--text)] outline-none transition focus:border-[#ffb100]'

function outcomeStyle(outcome: RemediationOutcome): string {
  if (outcome === 'succeeded') return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300'
  if (outcome === 'failed' || outcome === 'timed_out' || outcome === 'interrupted')
    return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
  if (outcome === 'running') return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
  return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300'
}

// The run log: every decision the consumer made, including skipped runs and why.
export function RunLog({ actions, initialRunId = null }: Props) {
  const { settings } = useSystemSettings()
  const [outcome, setOutcome] = useState<RemediationOutcome | ''>('')
  const [actionId, setActionId] = useState('')
  const [host, setHost] = useState('')
  const [debouncedHost, setDebouncedHost] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [page, setPage] = useState(1)

  const [items, setItems] = useState<RemediationRun[]>([])
  const [pages, setPages] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [selectedRun, setSelectedRun] = useState<number | null>(initialRunId)

  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedHost(host)
      setPage(1)
    }, 350)
    return () => clearTimeout(timeout)
  }, [host])

  useEffect(() => {
    let cancelled = false
    async function load() {
      setIsLoading(true)
      setLoadError(null)
      try {
        const data = await listRuns({
          page,
          perPage: PER_PAGE,
          action: actionId ? Number(actionId) : undefined,
          host: debouncedHost || undefined,
          outcome: outcome || undefined,
          from: from || undefined,
          to: to || undefined,
        })
        if (cancelled) return
        setItems(data.items)
        setPages(data.pages)
      } catch (err) {
        if (!cancelled) setLoadError(errorMessage(err, 'Unable to load the run log.'))
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [page, actionId, debouncedHost, outcome, from, to])

  const filtered = Boolean(outcome || actionId || debouncedHost || from || to)
  const change = <T,>(setter: (value: T) => void) => (value: T) => {
    setter(value)
    setPage(1)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="run-action" className="mb-1 block text-xs text-[var(--text-muted)]">Action</label>
          <select id="run-action" className={filterClass} value={actionId} onChange={(e) => change(setActionId)(e.target.value)}>
            <option value="">All actions</option>
            {actions.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="run-outcome" className="mb-1 block text-xs text-[var(--text-muted)]">Outcome</label>
          <select id="run-outcome" className={filterClass} value={outcome} onChange={(e) => change(setOutcome)(e.target.value as RemediationOutcome | '')}>
            <option value="">All outcomes</option>
            {(Object.keys(OUTCOME_LABELS) as RemediationOutcome[]).map((key) => (
              <option key={key} value={key}>{OUTCOME_LABELS[key]}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="run-host" className="mb-1 block text-xs text-[var(--text-muted)]">Host</label>
          <input id="run-host" className={`${filterClass} w-40`} value={host} onChange={(e) => setHost(e.target.value)} />
        </div>
        <div>
          <label htmlFor="run-from" className="mb-1 block text-xs text-[var(--text-muted)]">From</label>
          <input id="run-from" type="date" className={filterClass} value={from} onChange={(e) => change(setFrom)(e.target.value)} />
        </div>
        <div>
          <label htmlFor="run-to" className="mb-1 block text-xs text-[var(--text-muted)]">To</label>
          <input id="run-to" type="date" className={filterClass} value={to} onChange={(e) => change(setTo)(e.target.value)} />
        </div>
      </div>

      {loadError && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-300">
          {loadError}
        </div>
      )}

      {isLoading && items.length === 0 && !loadError && <p className="text-sm text-[var(--text-muted)]">Loading the run log…</p>}

      {!isLoading && !loadError && items.length === 0 && (
        <p className="rounded-xl border border-dashed border-[var(--border)] p-6 text-center text-sm text-[var(--text-muted)]">
          {filtered ? 'No runs match these filters.' : 'No runs yet.'}
        </p>
      )}

      {items.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--hover)] text-[var(--text-muted)]">
              <tr>
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">Host</th>
                <th className="px-4 py-3 font-medium">Service</th>
                <th className="px-4 py-3 font-medium">State</th>
                <th className="px-4 py-3 font-medium">Outcome</th>
                <th className="px-4 py-3 font-medium">Reason</th>
                <th className="px-4 py-3 font-medium">Operator</th>
                <th className="px-4 py-3 font-medium"><span className="sr-only">Details</span></th>
              </tr>
            </thead>
            <tbody>
              {items.map((run) => (
                <tr key={run.id} className="border-t border-[var(--border)] text-[var(--text)]">
                  <td className="whitespace-nowrap px-4 py-3">
                    {formatServerDateTime(run.receivedAt, settings.dateTimeFormat, settings.timeZone)}
                  </td>
                  <td className="px-4 py-3">{run.actionName}</td>
                  <td className="px-4 py-3">{run.hostname}</td>
                  <td className="px-4 py-3">{run.service ?? '—'}</td>
                  <td className="px-4 py-3">{run.state} ({run.stateType})</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${outcomeStyle(run.outcome)}`}>
                      {OUTCOME_LABELS[run.outcome] ?? run.outcome}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[var(--text-muted)]">{run.reason ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className={run.notifyState === 'failed' ? 'text-red-700 dark:text-red-300' : 'text-[var(--text)]'}>
                      {notifyLabel(run)}
                    </span>
                    {run.notifyError && <div className="text-xs text-[var(--text-muted)]">{run.notifyError}</div>}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      aria-label={`View run ${run.id}`}
                      onClick={() => setSelectedRun(run.id)}
                      className="rounded-lg p-2 text-[var(--text-muted)] hover:bg-[var(--hover)]"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pages > 1 && <Pagination page={page} pageCount={pages} onPageChange={setPage} variant="themed" disabled={isLoading} />}

      {selectedRun !== null && <RunDrawer runId={selectedRun} onClose={() => setSelectedRun(null)} />}
    </div>
  )
}
