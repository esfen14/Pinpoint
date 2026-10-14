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
      className="flex items-start justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-400"
    >
      <span>{message}</span>
      <button type="button" onClick={onDismiss} className="text-xs font-medium underline">
        Dismiss
      </button>
    </div>
  )
}
