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

export const OUTCOME_LABELS: Record<RemediationOutcome, string> = {
  running: 'Running',
  succeeded: 'Succeeded',
  failed: 'Failed',
  timed_out: 'Timed out',
  skipped_cooldown: 'Skipped (cooldown)',
  skipped_hourly_cap: 'Skipped (hourly limit)',
  interrupted: 'Interrupted',
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

/** Field name (for example "name" or "parameters.command") to the server's message. */
export type FieldErrors = Record<string, string>
