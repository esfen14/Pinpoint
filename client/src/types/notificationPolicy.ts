// Public JSON contract for the system-wide Nagios notification policy.
export type Weekday = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
export type HostNotificationOption = 'd' | 'u' | 'r' | 'f' | 's'
export type ServiceNotificationOption = 'w' | 'u' | 'c' | 'r' | 'f' | 's'

export interface QuietHourWindow {
  weekday: Weekday
  start: string
  end: string
}

export interface NotificationPolicy {
  quietHours: QuietHourWindow[]
  hostOptions: HostNotificationOption[]
  serviceOptions: ServiceNotificationOption[]
  renotifyInterval: number
  version: number
  /** The viewer's display time-zone preference does not affect quiet hours. */
  timeZone: string
}
