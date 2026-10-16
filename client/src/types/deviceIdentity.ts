import type { MonitoringState } from './host'

export type DeviceSummary = {
  id: number
  nagios_host_name: string
  display_name: string | null
  ip_address: string | null
  state: string
  monitoring_state: MonitoringState
  monitored: boolean
}
export type IdentityReview = {
  id: number
  kind: string
  message: string
  devices: DeviceSummary[]
  ip_address: string | null
  mac_address: string | null
  created_at: string
}
export type IdentityEvidence = {
  device: DeviceSummary
  confidence: string
  identifiers: { id: number; kind: string; value: string; strong: boolean; first_seen_at: string; last_seen_at: string }[]
  recommendation: string | null
}
export type AddressEvidence = {
  device: DeviceSummary
  addresses: { id: number; ip_address: string; current: boolean; first_seen_at: string; last_seen_at: string; closed_at: string | null }[]
}
export type MergeResult = { config_ok: boolean; config_applied: boolean; config_message: string }

export const IDENTITY_REVIEW_LABELS: Record<string, string> = {
  CONFLICT: 'Conflicting identifiers', IDENTITY_CHANGED: 'Device identity changed',
  IP_REUSE: 'IP address reused', DUPLICATE_IDENTITY: 'Duplicate identity', STATIC_MOVED: 'Static address moved',
}
export function identityReviews(items: IdentityReview[]) {
  return items.filter(item => Object.hasOwn(IDENTITY_REVIEW_LABELS, item.kind))
}
export function deviceLabel(device: DeviceSummary) {
  return `ID ${device.id} · ${device.display_name || device.nagios_host_name} · ${device.ip_address || 'IP unavailable'}`
}
