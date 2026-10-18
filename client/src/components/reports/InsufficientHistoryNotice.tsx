// Shown when a report ran successfully but Nagios has no recorded state for anything in it,
// for example right after a fresh install or a restart. Different from "no matching rows".
export function InsufficientHistoryNotice({ subject = 'these objects' }: { subject?: string }) {
  return (
    <p role="status" className="border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm text-gray-600 dark:border-white/10 dark:bg-white/5 dark:text-gray-300">
      Nagios has no recorded history for {subject} in this period, so there is nothing to measure yet.
      Try a later period, or wait for checks to run.
    </p>
  )
}
