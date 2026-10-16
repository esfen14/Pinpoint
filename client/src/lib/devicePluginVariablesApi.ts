// Wrappers around the per-device plugin variable routes in server/app/api/system/device_plugin_variables.py.
import { apiDelete, apiGet, apiPost, apiPut } from './api'
import type { DeviceVariablesResponse, SnmpSecretName, SnmpTestResult } from '../types/devicePluginVariables'

const path = (deviceId: number, plugin: string) => `/api/system/hosts/${deviceId}/plugin-variables/${plugin}`

// A response without the expected fields (anything but this route's answer) reads as "nothing saved, not in use".
function normalized(response: DeviceVariablesResponse): DeviceVariablesResponse {
  return {
    ...response,
    variables: response?.variables ?? {},
    secrets_set: response?.secrets_set ?? {},
    editable: response?.editable ?? [],
    in_use: response?.in_use ?? null,
  }
}

export function getDevicePluginVariables(deviceId: number, plugin = 'snmp') {
  return apiGet<DeviceVariablesResponse>(path(deviceId, plugin)).then(normalized)
}

// The variables replace the saved plain values; a password that is left out keeps its saved value.
export function saveDevicePluginVariables(
  deviceId: number,
  variables: Record<string, string | number>,
  clearSecrets: SnmpSecretName[] = [],
  plugin = 'snmp',
) {
  return apiPut<DeviceVariablesResponse>(path(deviceId, plugin), { variables, clear_secrets: clearSecrets }).then(normalized)
}

export function resetDevicePluginVariables(deviceId: number, plugin = 'snmp') {
  return apiDelete<DeviceVariablesResponse>(path(deviceId, plugin)).then(normalized)
}

// Asks the device once with the given settings (or the saved ones when none are given). Saves nothing.
export function testDeviceSnmp(deviceId: number, variables?: Record<string, string | number>) {
  return apiPost<SnmpTestResult>(`${path(deviceId, 'snmp')}/test`, variables ? { variables } : {})
}
