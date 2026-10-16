import { apiGet, apiPut } from './api'
import type { TopologyData } from '../types/topology'

export function getTopology() {
  return apiGet<TopologyData>('/api/system/topology')
}
export function setDeviceParents(deviceId: number, parentIds: number[]) {
  return apiPut(`/api/system/hosts/${deviceId}`, { parent_device_ids: parentIds })
}
