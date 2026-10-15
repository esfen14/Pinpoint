import { apiDelete, apiGet, apiPost, apiPut } from './api'
import type { Escalation, EscalationInput, EscalationList } from '../types/escalation'

export function getEscalations() {
  return apiGet<EscalationList>('/api/system/escalations')
}
export function createEscalation(data: EscalationInput) {
  return apiPost<Escalation>('/api/system/escalations', data)
}
export function updateEscalation(id: number, data: EscalationInput) {
  return apiPut<Escalation>(`/api/system/escalations/${id}`, data)
}
export function deleteEscalation(id: number) {
  return apiDelete<null>(`/api/system/escalations/${id}`)
}
