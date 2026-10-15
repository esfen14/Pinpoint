// Public JSON contract of server/app/api/system/maintenance.py.
// A maintenance window silences alerts through Nagios scheduled downtime. It is not
// Settings → System → Maintenance Mode, which only pauses PinPoint's own background jobs.

export type MaintenanceRecurrence = 'none' | 'daily' | 'weekly'
export type MaintenanceStatus = 'active' | 'cancelled' | 'completed'
export type OccurrenceStatus = 'pending' | 'sent' | 'failed' | 'cancelled'

export type MaintenanceOccurrence = {
  startAt: string
  endAt: string
  status: OccurrenceStatus
  attempts: number
  /** Why Nagios was not updated; set on a failed or retrying occurrence. */
  error: string | null
}

export type MaintenanceWindow = {
  id: number
  scope: { type: 'all' | 'device'; deviceId: number | null; deviceName: string | null }
  startAt: string
  endAt: string
  recurrence: MaintenanceRecurrence
  recurrenceUntil: string | null
  timeZone: string
  comment: string
  status: MaintenanceStatus
  nextOccurrence: { startAt: string; endAt: string } | null
  lastOccurrenceSent: string | null
  createdBy: string | null
  createdAt: string
  occurrences: MaintenanceOccurrence[]
}

export type MaintenanceDevice = { id: number; name: string }

export type MaintenanceList = { windows: MaintenanceWindow[]; devices: MaintenanceDevice[] }

/** Body of create and update. Times are ISO 8601 with a UTC offset. */
export type MaintenanceInput = {
  deviceId: number | null
  startAt: string
  endAt: string
  recurrence: MaintenanceRecurrence
  recurrenceUntil: string | null
  timeZone: string
  comment: string
}

/** Update and cancel also say whether Nagios could be told to delete existing downtime. */
export type MaintenanceChangeResult = MaintenanceWindow & {
  nagios_synced: boolean
  nagios_message: string | null
}
