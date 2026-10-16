import type { HostState, MonitoringState } from './host'

export type TopologyDevice = {
  id: number | null
  nagios_host_name: string
  display_name: string | null
  ip_address: string | null
  os: string | null
  last_seen_at: string | null
  last_check: string | null
  monitoring_state: MonitoringState | null
  host_state: HostState | null
  parent_device_ids: number[]
  editable: boolean
}
export type TopologyEdge = {
  child_id: number
  parent_id: number
  nagios_eligible: boolean
  omission_reason: string | null
}
export type TopologyData = {
  devices: TopologyDevice[]
  edges: TopologyEdge[]
  suggested_gateway_id: number | null
}

export function topologyNodeId(device: TopologyDevice): string {
  return device.id === null ? `host-${device.nagios_host_name}` : `device-${device.id}`
}
export function deviceLabel(device: TopologyDevice): string {
  return device.display_name || device.nagios_host_name
}
export function parentIsEligible(device: TopologyDevice): boolean {
  return device.id !== null && !!device.ip_address &&
    (device.monitoring_state === 'monitored' || device.monitoring_state === 'missing')
}
