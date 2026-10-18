// Mirrors the report endpoints exposed by server/app/api/system/report.py.

export type ReportPeriod = 'last_24h' | 'today' | 'last_7d' | 'last_30d' | 'last_90d' | 'custom'

export type PeriodMeta = {
  period: string
  start: string
  end: string
}

// --- GET /report/availability -----------------------------------------

export type HostAvailabilityRow = {
  hostname: string
  // The current Nagios state; null when current status could not be read for this host.
  state: string | null
  uptimePct: number | null
  totalSnapshots: number
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
  currentStatus: CurrentServiceStatus
  hosts: HostAvailabilityRow[]
}

type HostAvailabilityApiRecord = {
  hostname: string
  state: string | null
  uptime_pct: number | null
  total_snapshots: number
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
  current_status: CurrentServiceStatus
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
    currentStatus: data.current_status,
    hosts: data.hosts.map((h) => ({
      hostname: h.hostname,
      state: h.state,
      uptimePct: h.uptime_pct,
      totalSnapshots: h.total_snapshots,
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
