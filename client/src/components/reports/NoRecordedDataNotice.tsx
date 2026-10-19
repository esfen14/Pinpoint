// Shown when a host report lists hosts but none has any recorded state time in the period,
// so a table of dashes is not mistaken for a measured result.
export function NoRecordedDataNotice({ subject = 'these hosts' }: { subject?: string }) {
  return (
    <p role="status" className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">
      No data in this period. Nagios has no recorded history for {subject} in the selected period.
    </p>
  )
}
