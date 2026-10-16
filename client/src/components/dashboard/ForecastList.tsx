import { TrendingUp } from 'lucide-react'
import { useDisplayTime } from '../../hooks/useDisplayTime'
import { forecastBasis, metricLabel, timeUntil, type ForecastData } from '../../types/forecast'

type ForecastListProps = {
  data: ForecastData | null
  isLoading: boolean
  error: string | null
  // Injected so the wording is testable; defaults to the current time.
  now?: Date
}

/** Dashboard card listing the disk and memory metrics on course to reach a threshold, soonest first. */
export function ForecastList({ data, isLoading, error, now }: ForecastListProps) {
  const { formatDate } = useDisplayTime()
  const reference = now ?? new Date()
  const forecasts = data?.forecasts ?? []
  const waiting = data?.insufficient.length ?? 0

  let body
  if (isLoading) {
    body = <p className="py-6 text-center text-sm text-[var(--text-muted)]">Loading forecasts…</p>
  } else if (error) {
    body = <p className="py-6 text-center text-sm text-red-500">{error}</p>
  } else if (forecasts.length === 0 && waiting > 0) {
    body = (
      <p className="py-6 text-center text-sm text-[var(--text-muted)]">
        Not enough data yet for {waiting} {waiting === 1 ? 'service' : 'services'}. A trend needs about a day and a half of history.
      </p>
    )
  } else if (forecasts.length === 0) {
    body = <p className="py-6 text-center text-sm text-[var(--text-muted)]">Nothing is on course to reach a threshold.</p>
  } else {
    body = (
      <>
        <ul className="divide-y divide-[var(--border)]">
          {forecasts.map((f) => (
            <li key={`${f.hostname}-${f.serviceName}-${f.metric}`} className="py-3">
              <p className="text-sm font-medium text-[var(--text)]">
                {f.hostname} <span className="font-normal text-[var(--text-muted)]">· {f.serviceName}</span>
              </p>
              <p className="text-sm text-[var(--text)]">
                {metricLabel(f.metric)} may reach its {f.kind} level ({f.threshold}%) around {formatDate(f.crossingAt)},{' '}
                {timeUntil(f.crossingAt, reference)}
              </p>
              <p className="text-xs text-[var(--text-muted)]">
                Estimate {forecastBasis(f.windowHours)}; now at {Math.round(f.currentValue)}%.
              </p>
            </li>
          ))}
        </ul>
        {waiting > 0 && (
          <p className="mt-2 text-xs text-[var(--text-muted)]">
            {waiting} {waiting === 1 ? 'service has' : 'services have'} not been watched long enough to estimate yet.
          </p>
        )}
      </>
    )
  }

  return (
    <div className="rounded-2xl bg-[var(--card)] border border-[var(--border)] p-6 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-[var(--text-muted)]" />
        <h2 className="text-lg font-semibold text-[var(--text)]">Running out soon</h2>
      </div>
      <p className="mb-2 text-xs text-[var(--text-muted)]">
        Each date is an estimate from a straight-line trend of recent readings, not a failure. It is shown only so you can act early.
      </p>
      {body}
    </div>
  )
}
