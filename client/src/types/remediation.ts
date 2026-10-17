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

/** GET and PUT /api/system/remediation/settings: the kill switch and how long runs are kept. */
export interface RemediationSettings {
  enabled: boolean
  retentionDays: number
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
