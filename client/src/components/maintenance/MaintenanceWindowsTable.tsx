import { useDisplayTime } from '../../hooks/useDisplayTime'
import type { MaintenanceRecurrence, MaintenanceStatus, MaintenanceWindow } from '../../types/maintenance'

type Props = {
  windows: MaintenanceWindow[]
  /** Id of a window whose cancel is waiting for a second click. */
  confirmingId: number | null
  /** Id of a window being changed right now. */
  busyId: number | null
  onEdit: (window: MaintenanceWindow) => void
  onAskCancel: (window: MaintenanceWindow) => void
  onConfirmCancel: (window: MaintenanceWindow) => void
  onDismissCancel: () => void
}

const RECURRENCE_LABEL: Record<MaintenanceRecurrence, string> = { none: 'Once', daily: 'Every day', weekly: 'Every week' }
const STATUS_LABEL: Record<MaintenanceStatus, string> = { active: 'Scheduled', cancelled: 'Cancelled', completed: 'Completed' }
const STATUS_CLASS: Record<MaintenanceStatus, string> = {
  active: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  cancelled: 'bg-gray-500/10 text-gray-600 dark:text-gray-400',
  completed: 'bg-gray-500/10 text-gray-600 dark:text-gray-400',
}

const cell = 'px-4 py-3 align-top text-sm text-[var(--text)]'

export function MaintenanceWindowsTable({ windows, confirmingId, busyId, onEdit, onAskCancel, onConfirmCancel, onDismissCancel }: Props) {
  const { formatDateTime } = useDisplayTime()

  return (
    <div className="overflow-x-auto rounded-3xl border border-[var(--border)] bg-[var(--card)]">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--text-muted)]">
            <th className="px-4 py-3 font-medium">Devices</th>
            <th className="px-4 py-3 font-medium">Next occurrence</th>
            <th className="px-4 py-3 font-medium">Repeats</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Reason</th>
            <th className="px-4 py-3 font-medium"><span className="sr-only">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          {windows.map((window) => {
            const failed = window.occurrences.filter((occurrence) => occurrence.status === 'failed' || (occurrence.status === 'pending' && occurrence.error))
            return (
              <tr key={window.id} className="border-b border-[var(--border)] last:border-0">
                <td className={cell}>{window.scope.type === 'all' ? 'All monitored devices' : window.scope.deviceName ?? `Device ${window.scope.deviceId}`}</td>
                <td className={cell}>
                  {window.nextOccurrence ? (
                    <>
                      <div>{formatDateTime(window.nextOccurrence.startAt)}</div>
                      <div className="text-xs text-[var(--text-muted)]">until {formatDateTime(window.nextOccurrence.endAt)}</div>
                    </>
                  ) : (
                    '—'
                  )}
                </td>
                <td className={cell}>{RECURRENCE_LABEL[window.recurrence]}</td>
                <td className={cell}>
                  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASS[window.status]}`}>{STATUS_LABEL[window.status]}</span>
                  {failed.map((occurrence) => (
                    <div key={occurrence.startAt} role="alert" className="mt-2 text-xs text-red-600 dark:text-red-400">
                      {occurrence.status === 'failed' ? 'Failed' : 'Retrying'} for {formatDateTime(occurrence.startAt)}
                      {occurrence.error ? `: ${occurrence.error}` : ''}
                    </div>
                  ))}
                </td>
                <td className={cell}>{window.comment}</td>
                <td className={`${cell} whitespace-nowrap text-right`}>
                  {window.status === 'active' &&
                    (confirmingId === window.id ? (
                      <span className="inline-flex items-center gap-2">
                        <span className="text-xs text-[var(--text-muted)]">Cancel this window?</span>
                        <button type="button" disabled={busyId === window.id} onClick={() => onConfirmCancel(window)} className="rounded-lg bg-red-600 px-3 py-1 text-xs font-medium text-white disabled:opacity-50">
                          Yes, cancel it
                        </button>
                        <button type="button" onClick={onDismissCancel} className="rounded-lg border border-[var(--border)] px-3 py-1 text-xs text-[var(--text)]">
                          Keep it
                        </button>
                      </span>
                    ) : (
                      <span className="inline-flex gap-2">
                        <button type="button" aria-label={`Edit window ${window.id}`} onClick={() => onEdit(window)} className="rounded-lg border border-[var(--border)] px-3 py-1 text-xs text-[var(--text)]">
                          Edit
                        </button>
                        <button type="button" aria-label={`Cancel window ${window.id}`} onClick={() => onAskCancel(window)} className="rounded-lg border border-red-500/40 px-3 py-1 text-xs text-red-600 dark:text-red-400">
                          Cancel
                        </button>
                      </span>
                    ))}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
