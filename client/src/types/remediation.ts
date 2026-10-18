// Public JSON contract for /api/system/remediation (see Backend_Modules_and_Routes.md).
export type RemediationScope = 'service' | 'host'

export type RemediationOutcome =
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'timed_out'
  | 'skipped_cooldown'
  | 'skipped_hourly_cap'
  | 'interrupted'
  | 'skipped_kill_switch'
  | 'skipped_maintenance'
  | 'skipped_downtime'
  | 'skipped_acknowledged'

export const OUTCOME_LABELS: Record<RemediationOutcome, string> = {
  running: 'Running',
  succeeded: 'Succeeded',
  failed: 'Failed',
  timed_out: 'Timed out',
  skipped_cooldown: 'Skipped (cooldown)',
  skipped_hourly_cap: 'Skipped (hourly limit)',
  interrupted: 'Interrupted',
  skipped_kill_switch: 'Skipped (kill switch)',
  skipped_maintenance: 'Skipped (maintenance)',
  skipped_downtime: 'Skipped (downtime)',
  skipped_acknowledged: 'Skipped (acknowledged)',
}

/** A Nagios host name and the service names seen on it, suggested in the action form. */
export type RemediationTarget = { hostname: string; services: string[] }

export type NotifyKind = 'failed' | 'capped' | 'repeated'
export type NotifyState = 'pending' | 'sent' | 'failed'

export const NOTIFY_KINDS: NotifyKind[] = ['failed', 'capped', 'repeated']

/** Why the operator is told, in plain language (run drawer). */
export const NOTIFY_KIND_LABELS: Record<NotifyKind, string> = {
  failed: 'The action failed',
  capped: 'Stopped by its limits',
  repeated: 'Recovered repeatedly, fault persists',
}

/** The notification state of one run in plain language. A run with nothing due is "Not required". */
export function notifyLabel(run: Pick<RemediationRun, 'notifyKind' | 'notifyState'>): string {
  if (!run.notifyKind || !run.notifyState) return 'Not required'
  if (run.notifyState === 'sent') return 'Operator notified'
  if (run.notifyState === 'pending') return 'Notification pending'
  return 'Notification failed'
}

export interface ActionTypeInfo {
  key: string
  label: string
  description: string
  parameters: {
    name: string
    label: string
    type: 'choice' | 'text'
    choices?: string[]
    required?: boolean
  }[]
}

export interface RemediationAction {
  id: number
  name: string
  actionType: string
  scopeKind: RemediationScope
  hostPattern: string
  servicePattern: string | null
  parameters: Record<string, unknown>
  enabled: boolean
  maxRunsPerHour: number
  cooldownSeconds: number
  runWhenAcknowledged: boolean
  notifyOn: NotifyKind[]
  version: number
  updatedAt: string | null
  updatedBy: number | null
}

/** What the form sends; the server adds the id, version and audit fields. */
export interface RemediationActionInput {
  name: string
  actionType: string
  scopeKind: RemediationScope
  hostPattern: string
  servicePattern: string | null
  parameters: Record<string, unknown>
  enabled: boolean
  maxRunsPerHour: number
  cooldownSeconds: number
  runWhenAcknowledged: boolean
  notifyOn: NotifyKind[]
}

export interface RemediationRun {
  id: number
  actionId: number | null
  actionName: string
  hostname: string
  service: string | null
  state: string
  stateType: string
  attempt: number
  receivedAt: string
  startedAt: string | null
  finishedAt: string | null
  outcome: RemediationOutcome
  reason: string | null
  notifyKind: NotifyKind | null
  notifyState: NotifyState | null
  notifyAttempts: number
  notifyError: string | null
  notifyAt: string | null
}

/** One item of GET /api/system/remediation/last-runs: the newest run for a host and service. */
export interface LastRun {
  runId: number
  hostname: string
  service: string | null
  outcome: RemediationOutcome
  notifyState: NotifyState | null
  receivedAt: string
}

export interface RecoveryBadge {
  text: string
  title: string
  tone: 'good' | 'bad' | 'neutral'
}

/** The compact note under a service name: what automatic recovery last did, and whether the operator was told. */
export function recoveryBadgeFor(run: LastRun): RecoveryBadge {
  let badge: RecoveryBadge
  switch (run.outcome) {
    case 'succeeded':
      badge = { text: 'Auto-recovered', title: 'Automatic recovery restarted this service.', tone: 'good' }
      break
    case 'failed':
    case 'timed_out':
      badge = { text: 'Recovery failed', title: 'Automatic recovery tried and did not succeed.', tone: 'bad' }
      break
    case 'skipped_cooldown':
    case 'skipped_hourly_cap':
      badge = { text: 'Recovery limited', title: 'Automatic recovery was stopped by its cooldown or hourly limit.', tone: 'bad' }
      break
    case 'running':
      badge = { text: 'Recovering', title: 'Automatic recovery is running now.', tone: 'neutral' }
      break
    case 'interrupted':
      badge = { text: 'Recovery interrupted', title: 'PinPoint stopped while automatic recovery was running.', tone: 'bad' }
      break
    default:
      badge = { text: 'Recovery skipped', title: 'Automatic recovery decided not to act on this problem.', tone: 'neutral' }
  }
  if (run.notifyState === 'sent') badge.title += ' The operator was notified.'
  else if (run.notifyState === 'pending') badge.title += ' A notification is waiting to be sent.'
  else if (run.notifyState === 'failed') badge.title += ' The notification failed.'
  return badge
}

/** Key to look a service's last run up by host and name together. */
export function lastRunKey(hostname: string, service: string | null): string {
  return `${hostname}\u0000${service ?? ''}`
}

export interface RemediationRunDetail extends RemediationRun {
  output: string | null
}

export interface RemediationRunList {
  items: RemediationRun[]
  page: number
  per_page: number
  pages: number
  total: number
}

export interface RemediationRunFilters {
  page: number
  perPage: number
  action?: number
  host?: string
  outcome?: RemediationOutcome
  from?: string
  to?: string
}

/** GET /api/system/remediation/health: whether the consumer that runs actions is working. */
export interface RemediationHealth {
  lastTickAt: string | null
  lastError: string | null
  stalled: boolean
  backlog: number
  oldestSpoolAgeSeconds: number | null
  runsLast24h: number
  capsHitLast24h: number
  skippedLast24h: number
  droppedTotal: number
  droppedAt: string | null
}

/**
 * GET and PUT /api/system/remediation/settings: the kill switch, how long runs are kept, and the
 * repeat-recovery limits (this many successful recoveries of one service inside the window send
 * one "repeated" notification).
 */
export interface RemediationSettings {
  enabled: boolean
  retentionDays: number
  repeatCount: number
  repeatWindowHours: number
}

/** Field name (for example "name" or "parameters.command") to the server's message. */
export type FieldErrors = Record<string, string>

/** GET and PUT /api/system/remediation/services/<host>/<service>: one service's "Recover automatically" setting. */
export interface ServiceRecovery {
  hostname: string
  service: string
  enabled: boolean
  maxRestartsPerHour: number
  /** Null until the setting exists; send it back on every change. */
  version: number | null
  actionId: number | null
  actionType: string | null
  /** The unit the server chose (read-only; the request never carries one). */
  unit: string | null
  canEnable: boolean
  /** Why the switch cannot be turned on, in plain words. */
  reason: string | null
  otherActions: { id: number; name: string }[]
  lastRun: RemediationRun | null
}

export interface ServiceRecoveryInput {
  enabled: boolean
  maxRestartsPerHour: number
  version: number | null
}

export const MIN_RESTARTS_PER_HOUR = 1
export const MAX_RESTARTS_PER_HOUR = 6

/** Key for a set of services that recover automatically (host and service never contain a tab). */
export function recoveryKey(hostname: string, service: string) {
  return `${hostname}\t${service}`
}
