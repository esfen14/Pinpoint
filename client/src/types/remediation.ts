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
