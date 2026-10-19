type NagiosWarningProps = { stopped: boolean }

/** Keep the stopped/stale monitoring warning visible without opening a detail row. */
export function NagiosWarning({ stopped }: NagiosWarningProps) {
  return (
    <div role="alert" className="mb-3 rounded-xl border border-red-400 bg-red-50 p-3 text-sm text-red-800 dark:border-red-700 dark:bg-red-950 dark:text-red-200">
      <p className="font-semibold">{stopped ? 'Nagios is not running.' : 'Nagios is not reporting current status.'} Displayed data may be stale.</p>
      <p>While stopped, Nagios is not checking hosts or services. Host and service states will not change while Nagios is stopped. Check the monitoring engine and its status polling.</p>
    </div>
  )
}
