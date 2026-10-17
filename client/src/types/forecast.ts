// Mirrors GET /api/system/forecast (server/app/api/system/forecast.py).
// A forecast is an estimate from a straight-line trend of stored performance data. It is for
// display only and never changes a service's Nagios state.

export type ForecastKind = 'warning' | 'critical'

export type Forecast = {
  hostname: string
  serviceName: string
  metric: string
  kind: ForecastKind
  threshold: number
  crossingAt: string
  slopePerHour: number
  rSquared: number
  sampleCount: number
  windowHours: number
  currentValue: number
  unit: string | null
  computedAt: string
}

// A service that has not been watched long enough to forecast yet.
export type WaitingSeries = {
  hostname: string
  serviceName: string
  metric: string
  sampleCount: number
  windowHours: number
}

export type ForecastData = {
  forecasts: Forecast[]
  insufficient: WaitingSeries[]
}

type ForecastApiRecord = {
  hostname: string
  service_name: string
  metric: string
  kind: string
  threshold: number
  crossing_at: string
  slope_per_hour: number
  r_squared: number
  sample_count: number
  window_hours: number
  current_value: number
  unit: string | null
  computed_at: string
}

type WaitingApiRecord = {
  hostname: string
  service_name: string
  metric: string
  sample_count: number
  window_hours: number
}

export type ForecastApiResponse = {
  forecasts?: ForecastApiRecord[]
  insufficient?: WaitingApiRecord[]
}

/** Convert the wire response; a response without the forecast fields is an empty result. */
export function fromForecastResponse(response: ForecastApiResponse): ForecastData {
  return {
    forecasts: (response.forecasts ?? []).map((r) => ({
      hostname: r.hostname,
      serviceName: r.service_name,
      metric: r.metric,
      kind: r.kind === 'critical' ? 'critical' : 'warning',
      threshold: r.threshold,
      crossingAt: r.crossing_at,
      slopePerHour: r.slope_per_hour,
      rSquared: r.r_squared,
      sampleCount: r.sample_count,
      windowHours: r.window_hours,
      currentValue: r.current_value,
      unit: r.unit,
      computedAt: r.computed_at,
    })),
    insufficient: (response.insufficient ?? []).map((r) => ({
      hostname: r.hostname,
      serviceName: r.service_name,
      metric: r.metric,
      sampleCount: r.sample_count,
      windowHours: r.window_hours,
    })),
  }
}

/** Plain-language name of a forecast metric. */
export function metricLabel(metric: string): string {
  if (metric.startsWith('disk/')) return 'Disk space used'
  if (metric.startsWith('memory/')) return 'Memory used'
  return metric
}

/** "based on the last 3 days" or "based on the last 36 hours". */
export function forecastBasis(windowHours: number): string {
  if (windowHours >= 48) return `based on the last ${Math.round(windowHours / 24)} days`
  return `based on the last ${Math.round(windowHours)} hours`
}

/** "in about 6 days", "in about 5 hours" or "in less than an hour". */
export function timeUntil(crossingAt: string, now: Date): string {
  const hours = (new Date(crossingAt).getTime() - now.getTime()) / 3_600_000
  if (hours < 1) return 'in less than an hour'
  if (hours < 24) {
    const whole = Math.round(hours)
    return `in about ${whole} ${whole === 1 ? 'hour' : 'hours'}`
  }
  const days = Math.max(1, Math.round(hours / 24))
  return `in about ${days} ${days === 1 ? 'day' : 'days'}`
}

export type ServiceForecastBadge =
  | { state: 'forecast'; text: string; title: string }
  | { state: 'waiting'; text: string; title: string }

/**
 * The badge for one service row: its soonest forecast, else "not enough data yet", else none.
 * Forecasts arrive soonest first, so the first match is the nearest crossing.
 */
export function forecastBadgeFor(
  data: ForecastData | null | undefined,
  hostname: string,
  serviceName: string,
  now: Date,
): ServiceForecastBadge | null {
  if (!data) return null
  const forecast = data.forecasts.find((f) => f.hostname === hostname && f.serviceName === serviceName)
  if (forecast) {
    return {
      state: 'forecast',
      text: `Estimate: ${forecast.kind} level ${timeUntil(forecast.crossingAt, now)}`,
      title:
        `${metricLabel(forecast.metric)} is estimated to reach its ${forecast.kind} level ` +
        `(${forecast.threshold}%) ${timeUntil(forecast.crossingAt, now)}, ${forecastBasis(forecast.windowHours)}. ` +
        'This is a trend estimate, not a failure.',
    }
  }
  const waiting = data.insufficient.find((w) => w.hostname === hostname && w.serviceName === serviceName)
  if (waiting) {
    return {
      state: 'waiting',
      text: 'Not enough data yet',
      title: 'This service has not been watched long enough to estimate a trend.',
    }
  }
  return null
}
