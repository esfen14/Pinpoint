// Public wire records; the form labels explain the Nagios notification counts.
export interface EscalationInput {
  first_notification: number
  last_notification: number
  interval_minutes: number
  contact_group: string
  host_id: number | null
}
export interface Escalation extends EscalationInput {
  id: number
  active: boolean
  reason: string
}
export interface EscalationList {
  items: Escalation[]
  groups: { name: string; member_count: number }[]
  hosts: { id: number; name: string }[]
}
