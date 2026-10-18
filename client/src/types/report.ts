// Mirrors the report endpoints exposed by server/app/api/system/report.py.

export type ReportPeriod = 'last_24h' | 'today' | 'last_7d' | 'last_30d' | 'last_90d' | 'custom'

export type ReportTimeZone = { name: string; utc_offset_seconds: number }

export type PeriodMeta = {
  period: string
  start: string
  end: string
  time_zone?: ReportTimeZone
}

// --- GET /report/availability -----------------------------------------

export type HostAvailabilityRow = {
  hostname: string
  state: string
  uptimePct: number | null
  upSeconds: number
  downSeconds: number
  unreachableSeconds: number
  knownSeconds: number
  lastCheck: string | null
  lastStateChange: string | null
}

export type HostAvailabilityReport = {
  period: PeriodMeta
  summary: {
    total: number
    up: number
    down: number
    unreachable: number
    uptimePct: number | null
  }
  hosts: HostAvailabilityRow[]
}

type HostAvailabilityApiRecord = {
  hostname: string
  state: string
  uptime_pct: number | null
  up_seconds: number
  down_seconds: number
  unreachable_seconds: number
  known_seconds: number
  last_check: string | null
  last_state_change: string | null
}

type HostAvailabilityApiResponse = {
  period: PeriodMeta
  summary: {
    total: number
    up: number
    down: number
    unreachable: number
    uptime_pct: number | null
  }
  hosts: HostAvailabilityApiRecord[]
}

export function fromHostAvailabilityResponse(data: HostAvailabilityApiResponse): HostAvailabilityReport {
  return {
    period: data.period,
    summary: {
      total: data.summary.total,
      up: data.summary.up,
      down: data.summary.down,
      unreachable: data.summary.unreachable,
      uptimePct: data.summary.uptime_pct,
    },
    hosts: data.hosts.map((h) => ({
      hostname: h.hostname,
      state: h.state,
      uptimePct: h.uptime_pct,
      upSeconds: h.up_seconds,
      downSeconds: h.down_seconds,
      unreachableSeconds: h.unreachable_seconds,
      knownSeconds: h.known_seconds,
      lastCheck: h.last_check,
      lastStateChange: h.last_state_change,
    })),
  }
}

// --- GET /report/network-services ---------------------------------------

export type ServiceDurations = {
  ok_seconds: number
  warning_seconds: number
  critical_seconds: number
  unknown_seconds: number
  scheduled_ok_seconds: number
  scheduled_warning_seconds: number
  scheduled_critical_seconds: number
  scheduled_unknown_seconds: number
  known_seconds: number
  no_data_seconds: number
  nagios_not_running_seconds: number
  unaccounted_seconds: number
  no_recorded_data_seconds: number
  window_seconds: number
}

export type CurrentServiceStatus = {
  available: boolean
  observed_at: string | null
  notice: string | null
}

export type ServiceInstance = ServiceDurations & {
  hostname: string
  service: string
  state: string | null
  uptime_pct: number | null
  last_check: string | null
  last_state_change: string | null
  plugin_output: string | null
}

export type ServiceRow = ServiceDurations & {
  service: string
  totalInstances: number
  ok: number
  warning: number
  critical: number
  unknown: number
  pending: number
  unavailable: number
  uptimePct: number | null
  instances: ServiceInstance[]
}

export type NetworkServicesReport = {
  period: PeriodMeta
  current_status: CurrentServiceStatus
  summary: ServiceDurations & {
    totalServices: number
    totalInstances: number
    ok: number
    warning: number
    critical: number
    unknown: number
    pending: number
    unavailable: number
    uptimePct: number | null
  }
  services: ServiceRow[]
}

type ServiceApiRecord = ServiceDurations & {
  service: string
  total_instances: number
  ok: number
  warning: number
  critical: number
  unknown: number
  pending: number
  unavailable: number
  uptime_pct: number | null
  instances: ServiceInstance[]
}

type NetworkServicesApiResponse = {
  period: PeriodMeta
  current_status: CurrentServiceStatus
  summary: ServiceDurations & {
    total_services: number
    total_instances: number
    ok: number
    warning: number
    critical: number
    unknown: number
    pending: number
    unavailable: number
    uptime_pct: number | null
  }
  services: ServiceApiRecord[]
}

export type DeviceServicesReport = {
  period: PeriodMeta
  current_status: CurrentServiceStatus
  summary: ServiceDurations & { uptime_pct: number | null }
  total_hosts: number
  total_services: number
  hosts: (ServiceDurations & { hostname: string; uptime_pct: number | null; services: ServiceInstance[] })[]
}

function durations(row: ServiceDurations): ServiceDurations {
  return {
    ok_seconds: row.ok_seconds, warning_seconds: row.warning_seconds,
    critical_seconds: row.critical_seconds, unknown_seconds: row.unknown_seconds,
    scheduled_ok_seconds: row.scheduled_ok_seconds, scheduled_warning_seconds: row.scheduled_warning_seconds,
    scheduled_critical_seconds: row.scheduled_critical_seconds, scheduled_unknown_seconds: row.scheduled_unknown_seconds,
    known_seconds: row.known_seconds, no_data_seconds: row.no_data_seconds,
    nagios_not_running_seconds: row.nagios_not_running_seconds,
    unaccounted_seconds: row.unaccounted_seconds, no_recorded_data_seconds: row.no_recorded_data_seconds,
    window_seconds: row.window_seconds,
  }
}

export function fromNetworkServicesResponse(data: NetworkServicesApiResponse): NetworkServicesReport {
  return {
    period: data.period,
    current_status: data.current_status,
    summary: {
      ...durations(data.summary),
      totalServices: data.summary.total_services,
      totalInstances: data.summary.total_instances,
      ok: data.summary.ok, warning: data.summary.warning,
      critical: data.summary.critical, unknown: data.summary.unknown,
      pending: data.summary.pending, unavailable: data.summary.unavailable,
      uptimePct: data.summary.uptime_pct,
    },
    services: data.services.map((s) => ({
      ...durations(s), service: s.service, totalInstances: s.total_instances,
      ok: s.ok, warning: s.warning, critical: s.critical, unknown: s.unknown,
      pending: s.pending, unavailable: s.unavailable, uptimePct: s.uptime_pct,
      instances: s.instances,
    })),
  }
}


// --- GET /report/availability-detail ------------------------------------

export type DetailState = {
  state: string
  seconds: number
  scheduled_seconds: number
  unscheduled_seconds: number
  pct_of_total: number | null
  pct_of_known: number | null
}

export type DetailInterval = {
  start: number
  end: number
  duration_seconds: number
  state: string
  information: string
  clipped_start: boolean
  unknown_onset: boolean
  continuing: boolean
}

export type AvailabilityDetail = {
  period: PeriodMeta
  source: string
  generated_at: string
  object: { hostname: string; service: string | null }
  totals: {
    window_seconds: number
    known_seconds: number
    no_recorded_data_seconds: number
    no_data_seconds: number
    nagios_not_running_seconds: number
    unaccounted_seconds: number
    states: DetailState[]
  }
  complete: boolean
  intervals_available: boolean
  intervals: DetailInterval[]
  reconciliation: { matches: boolean; tolerance_seconds: number; differences: Record<string, number> } | null
  notice: string | null
}

// --- Event filters, alert summary and histogram -------------------------

export type EventScope = 'both' | 'host' | 'service'
export type EventStateType = 'default' | 'hard' | 'soft' | 'both'
export type HistogramBreakdown = 'month' | 'day_of_month' | 'weekday' | 'hour'

export type EventFilterMeta = {
  scope: string
  state_type: string
  include_recoveries: boolean
  include_initial: boolean
  hostname: string | null
  service: string | null
  states: string[]
  policy: string
}

export type SummaryRow = {
  rank: number
  hostname: string
  service: string | null
  total: number
  states: Record<string, number>
  first: number
  last: number
}

export type AlertSummary = {
  period: PeriodMeta
  source: string
  generated_at: string
  filters: EventFilterMeta
  by: 'host' | 'service'
  complete: boolean
  notice: string | null
  totals: {
    problem_events: number
    recovery_events: number
    host_problem_events: number
    service_problem_events: number
    distinct_hosts: number
    distinct_objects: number
    states: Record<string, number>
  } | null
  ranking: SummaryRow[]
  top: SummaryRow[]
}

export type HistogramBucket = { label: string; total: number; states: Record<string, number> }

export type AlertHistogram = {
  period: PeriodMeta
  source: string
  generated_at: string
  filters: EventFilterMeta
  complete: boolean
  recurring: boolean
  bucketing_note: string
  notice: string | null
  breakdown: HistogramBreakdown
  buckets: HistogramBucket[]
  series: Record<string, number[]>
  total: number | null
}
