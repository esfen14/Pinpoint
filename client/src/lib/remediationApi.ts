import { ApiError, apiDelete, apiGet, apiPost, apiPut } from './api'
import type {
  ActionTypeInfo,
  FieldErrors,
  RemediationAction,
  RemediationActionInput,
  RemediationHealth,
  RemediationRunDetail,
  RemediationRunFilters,
  RemediationRunList,
  RemediationSettings,
  ServiceRecovery,
  ServiceRecoveryInput,
} from '../types/remediation'

const BASE = '/api/system/remediation'

export function getActionTypes() {
  return apiGet<{ items: ActionTypeInfo[] }>(`${BASE}/action-types`).then((data) => data.items)
}

export function listActions() {
  return apiGet<{ items: RemediationAction[] }>(`${BASE}/actions`).then((data) => data.items)
}

export function createAction(input: RemediationActionInput) {
  return apiPost<RemediationAction>(`${BASE}/actions`, input)
}

export function updateAction(id: number, input: RemediationActionInput, version: number) {
  return apiPut<RemediationAction>(`${BASE}/actions/${id}`, { ...input, version })
}

export function deleteAction(id: number) {
  return apiDelete<null>(`${BASE}/actions/${id}`)
}

export function listRuns(filters: RemediationRunFilters) {
  const params = new URLSearchParams({ page: String(filters.page), per_page: String(filters.perPage) })
  if (filters.action !== undefined) params.set('action', String(filters.action))
  if (filters.host) params.set('host', filters.host)
  if (filters.outcome) params.set('outcome', filters.outcome)
  if (filters.from) params.set('from', filters.from)
  if (filters.to) params.set('to', filters.to)
  return apiGet<RemediationRunList>(`${BASE}/runs?${params.toString()}`)
}

export function getRun(id: number) {
  return apiGet<RemediationRunDetail>(`${BASE}/runs/${id}`)
}

export function getHealth() {
  return apiGet<RemediationHealth>(`${BASE}/health`)
}

export function getSettings() {
  return apiGet<RemediationSettings>(`${BASE}/settings`)
}

export function updateSettings(changes: Partial<RemediationSettings>) {
  return apiPut<RemediationSettings>(`${BASE}/settings`, changes)
}

function servicePath(hostname: string, service: string) {
  const encodedService = service.split('/').map(encodeURIComponent).join('/')
  return `${BASE}/services/${encodeURIComponent(hostname)}/${encodedService}`
}

export function getServiceRecovery(hostname: string, service: string) {
  return apiGet<ServiceRecovery>(servicePath(hostname, service))
}

export function saveServiceRecovery(hostname: string, service: string, input: ServiceRecoveryInput) {
  const { version, ...rest } = input
  return apiPut<ServiceRecovery>(servicePath(hostname, service), version === null ? rest : { ...rest, version })
}

/** The per-field messages of a 400 response, or an empty object for any other error. */
export function fieldErrors(err: unknown): FieldErrors {
  if (err instanceof ApiError && err.status === 400) {
    const fields = (err.data as { fields?: unknown } | undefined)?.fields
    if (fields && typeof fields === 'object') return fields as FieldErrors
  }
  return {}
}
