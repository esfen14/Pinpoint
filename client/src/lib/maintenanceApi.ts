import { apiGet, apiPost, apiPut } from './api'
import type { MaintenanceChangeResult, MaintenanceInput, MaintenanceList, MaintenanceWindow } from '../types/maintenance'

const BASE = '/api/system/maintenance/windows'

export function listMaintenanceWindows() {
  return apiGet<MaintenanceList>(BASE)
}

export function createMaintenanceWindow(input: MaintenanceInput) {
  return apiPost<MaintenanceWindow>(BASE, input)
}

export function updateMaintenanceWindow(id: number, input: MaintenanceInput) {
  return apiPut<MaintenanceChangeResult>(`${BASE}/${id}`, input)
}

export function cancelMaintenanceWindow(id: number) {
  return apiPost<MaintenanceChangeResult>(`${BASE}/${id}/cancel`)
}
