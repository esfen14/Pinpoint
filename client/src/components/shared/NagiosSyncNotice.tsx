type Props = {
  message: string | null
  onDismiss: () => void
}

// Shown when an acknowledgement was saved in PinPoint but Nagios was not told.
export function NagiosSyncNotice({ message, onDismiss }: Props) {
  if (!message) return null
  return (
    <div
      role="status"
      className="flex items-start justify-between gap-3 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-700/50 dark:bg-amber-900/20 dark:text-amber-300"
    >
      <span>{message}</span>
      <button type="button" onClick={onDismiss} className="text-xs font-medium underline">
        Dismiss
      </button>
    </div>
  )
}
