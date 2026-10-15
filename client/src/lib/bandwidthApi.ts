// Wrappers around the bandwidth routes (network_health_activity.py) and the device interface routes
// (device_interfaces.py) in server/app/api/system.
import { apiGet, apiPost, apiPut } from './api'
import {
  fromBandwidthChoicesResponse,
  fromBandwidthResponse,
  type Bandwidth,
  type BandwidthApiResponse,
  type BandwidthDevice,
  type DeviceInterfacesResponse,
  type InterfaceChangeResult,
} from '../types/bandwidth'

export function getBandwidthChoices(): Promise<BandwidthDevice[]> {
  return apiGet<Parameters<typeof fromBandwidthChoicesResponse>[0]>(
    '/api/system/network-health/bandwidth/interfaces',
  ).then(fromBandwidthChoicesResponse)
}

// hours is 1, 6, 24 or 168: the server refuses any other window.
export function getBandwidth(hostname: string, ifIndex: number, hours: number): Promise<Bandwidth> {
  const query = new URLSearchParams({ hostname, interface: String(ifIndex), hours: String(hours) })
  return apiGet<BandwidthApiResponse>(`/api/system/network-health/bandwidth?${query}`).then(fromBandwidthResponse)
}

// A response without a list (anything but the interface routes' answer) is an empty, non-SNMP device.
function withInterfaces<T extends DeviceInterfacesResponse>(response: T): T {
  return { ...response, snmp: !!response?.snmp, interfaces: response?.interfaces ?? [] }
}

export function getDeviceInterfaces(deviceId: number) {
  return apiGet<DeviceInterfacesResponse>(`/api/system/hosts/${deviceId}/interfaces`).then(withInterfaces)
}

// Reads the interface list from the device over SNMP (needs system.hosts.edit).
export function refreshDeviceInterfaces(deviceId: number) {
  return apiPost<DeviceInterfacesResponse>(`/api/system/hosts/${deviceId}/interfaces/refresh`).then(withInterfaces)
}

export function setInterfaceMonitored(deviceId: number, ifIndex: number, monitored: boolean) {
  return apiPut<InterfaceChangeResult>(`/api/system/hosts/${deviceId}/interfaces/${ifIndex}`, { monitored })
}
