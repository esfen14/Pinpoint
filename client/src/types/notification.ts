// Mirrors GET /api/system/notifications — raw Nagios archivejson notification
// events (not normalized server-side, unlike dashboard.py's own notification
// feed), annotated with a per-user is_read flag. Field names vary between
// archivejson versions, so this mapper is tolerant of multiple aliases —
// mirrors the same normalization dashboard.py's _normalize_notification does.

export type NotificationSource = 'nagios' | 'pinpoint'

export type NotificationItem = {
  id: string
  source: NotificationSource
  timestamp: number
  type: string
  state: string
  hostname: string
  serviceName: string | null
  message: string
  fullMessage: string
  isRead: boolean
  repeatCount: number
  // A Nagios custom notification (for example one PinPoint sent when automatic recovery failed).
  // `comment` is its text, rebuilt by the server from PinPoint's own record; null when no run here sent it.
  isCustom: boolean
  comment: string | null
}

type RawNotification = Record<string, unknown> & { is_read: boolean; repeat_count?: number }

function str(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

export function fromRawNotification(raw: RawNotification, index: number): NotificationItem {
  const timestamp = (() => {
    const rawTs = typeof raw.timestamp === 'number' ? raw.timestamp : 0
    return rawTs > 9_999_999_999 ? Math.floor(rawTs / 1000) : rawTs
  })()

  if (raw.source === 'pinpoint') {
    const fullMessage = str(raw.message)
    return {
      id: `pinpoint-${String(raw.id ?? index)}`,
      source: 'pinpoint',
      timestamp,
      type: 'SCAN',
      state: str(raw.state).toUpperCase(),
      hostname: 'Pinpoint',
      serviceName: str(raw.title) || null,
      message: fullMessage.slice(0, 200),
      fullMessage,
      isRead: raw.is_read,
      repeatCount: 1,
      isCustom: false,
      comment: null,
    }
  }

  const hostname = str(raw.hostname) || str(raw.host_name)
  const output = str(raw.output) || str(raw.plugin_output) || str(raw.notificationreason) || str(raw.state)
  const type = (str(raw.notificationtype) || str(raw.type)).toUpperCase()
  const isCustom = raw.is_custom === true || type === 'CUSTOM'
  const comment = isCustom ? str(raw.comment) || null : null
  // A custom notification shows its comment first and keeps the plugin output in the detail.
  const fullMessage = comment ? `${comment}\n${output}`.trim() : output

  return {
    id: `${hostname}-${timestamp}-${index}`,
    source: 'nagios',
    timestamp,
    type,
    state: (str(raw.notificationreason) || str(raw.state)).toUpperCase(),
    hostname,
    serviceName: str(raw.servicedesc) || str(raw.description) || null,
    message: (comment ?? output).slice(0, 200),
    fullMessage,
    isRead: raw.is_read,
    repeatCount: typeof raw.repeat_count === 'number' ? raw.repeat_count : 1,
    isCustom,
    comment,
  }
}

/** Heading for one notification in the bell panel. */
export function notificationTitle(n: NotificationItem): string {
  if (n.source === 'pinpoint') return n.serviceName ?? 'Pinpoint notification'
  const kind = n.isCustom ? 'Custom notification' : n.type
  return `${kind} ${n.hostname || 'Unknown host'}${n.serviceName ? ` / ${n.serviceName}` : ''}`.trim()
}

export type NotificationsResponse = {
  last_seen_ts: number
  unread_count: number
  notifications: RawNotification[]
}

export function formatRelativeTime(unixSeconds: number, formatOlderDate?: (ms: number) => string): string {
  const diffMs = Date.now() - unixSeconds * 1000
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays}d ago`
  return formatOlderDate ? formatOlderDate(unixSeconds * 1000) : new Date(unixSeconds * 1000).toLocaleDateString()
}
