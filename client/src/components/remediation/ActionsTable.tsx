import { Pencil, Trash2 } from 'lucide-react'
import type { RemediationAction } from '../../types/remediation'

type Props = {
  actions: RemediationAction[]
  typeLabels: Record<string, string>
  canManage: boolean
  // The action whose switch or delete is in progress, so it cannot be double-clicked.
  busyId: number | null
  // True when the kill switch has stopped all automatic recovery.
  killSwitchOn: boolean
  onToggle: (action: RemediationAction) => void
  onEdit: (action: RemediationAction) => void
  onDelete: (action: RemediationAction) => void
}

/** What an action covers, for example "web-* / HTTP" or "web-01" for a host action. */
function coverage(action: RemediationAction): string {
  return action.scopeKind === 'service' && action.servicePattern
    ? `${action.hostPattern} / ${action.servicePattern}`
    : action.hostPattern
}

export function ActionsTable({ actions, typeLabels, canManage, busyId, killSwitchOn, onToggle, onEdit, onDelete }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
      <table className="w-full text-left text-sm">
        <thead className="bg-[var(--hover)] text-[var(--text-muted)]">
          <tr>
            <th className="px-4 py-3 font-medium">Enabled</th>
            <th className="px-4 py-3 font-medium">Name</th>
            <th className="px-4 py-3 font-medium">Type</th>
            <th className="px-4 py-3 font-medium">Applies to</th>
            <th className="px-4 py-3 font-medium">Limits</th>
            {canManage && <th className="px-4 py-3 font-medium">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {actions.map((action) => (
            <tr key={action.id} className="border-t border-[var(--border)] text-[var(--text)]">
              <td className="px-4 py-3">
                <button
                  type="button"
                  role="switch"
                  aria-checked={action.enabled}
                  aria-label={`Enable ${action.name}`}
                  disabled={!canManage || busyId === action.id}
                  onClick={() => onToggle(action)}
                  className={`relative h-6 w-11 rounded-full transition disabled:cursor-not-allowed disabled:opacity-60 ${
                    action.enabled ? 'bg-emerald-500' : 'bg-gray-300 dark:bg-white/20'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
                      action.enabled ? 'left-[22px]' : 'left-0.5'
                    }`}
                  />
                </button>
                {killSwitchOn && action.enabled && (
                  <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">Paused by the kill switch</p>
                )}
              </td>
              <td className="px-4 py-3 font-medium">{action.name}</td>
              <td className="px-4 py-3">{typeLabels[action.actionType] ?? action.actionType}</td>
              <td className="px-4 py-3">
                <span className="text-[var(--text-muted)]">{action.scopeKind === 'service' ? 'Service: ' : 'Host: '}</span>
                {coverage(action)}
              </td>
              <td className="px-4 py-3 text-[var(--text-muted)]">
                {action.maxRunsPerHour}/hour, {action.cooldownSeconds}s cooldown
              </td>
              {canManage && (
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      type="button"
                      aria-label={`Edit ${action.name}`}
                      onClick={() => onEdit(action)}
                      className="rounded-lg p-2 text-[var(--text-muted)] hover:bg-[var(--hover)]"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      aria-label={`Delete ${action.name}`}
                      disabled={busyId === action.id}
                      onClick={() => onDelete(action)}
                      className="rounded-lg p-2 text-red-600 hover:bg-red-50 disabled:opacity-60 dark:hover:bg-red-900/20"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
