import { beforeEach, describe, expect, it, vi } from 'vitest'

const http = vi.hoisted(() => ({ apiGet: vi.fn(), apiPost: vi.fn(), apiPut: vi.fn() }))
vi.mock('../lib/api', () => http)

import {
  getBandwidth,
  getBandwidthChoices,
  getDeviceInterfaces,
  refreshDeviceInterfaces,
  setInterfaceMonitored,
} from '../lib/bandwidthApi'

beforeEach(() => {
  http.apiGet.mockReset()
  http.apiPost.mockReset()
  http.apiPut.mockReset()
})

describe('bandwidth api', () => {
  it('asks for one interface and one allowed window, with the host name encoded', async () => {
    http.apiGet.mockResolvedValue({
      hostname: 'a b', interface: { if_index: 2, name: 'eth0', speed_bps: 1000 }, hours: 6, status: 'ok',
      in_points: [{ bucket_start: 't', bps: 5 }], out_points: [{ bucket_start: 't', bps: null }],
      latest: { timestamp: 't', in_bps: 5, out_bps: null, in_utilisation_pct: 0.5, out_utilisation_pct: null },
    })

    const result = await getBandwidth('a b', 2, 6)

    expect(http.apiGet).toHaveBeenCalledWith('/api/system/network-health/bandwidth?hostname=a+b&interface=2&hours=6')
    expect(result).toEqual({
      hostname: 'a b', interface: { ifIndex: 2, name: 'eth0', speedBps: 1000 }, hours: 6, status: 'ok',
      inPoints: [{ bucketStart: 't', bps: 5 }], outPoints: [{ bucketStart: 't', bps: null }],
      latest: { timestamp: 't', inBps: 5, outBps: null, inUtilisationPct: 0.5, outUtilisationPct: null },
    })
  })

  it('keeps a missing "latest" as null', async () => {
    http.apiGet.mockResolvedValue({
      hostname: 'h', interface: { if_index: 3, name: null, speed_bps: null }, hours: 1, status: 'insufficient_data',
      in_points: [], out_points: [], latest: null,
    })
    expect((await getBandwidth('h', 3, 1)).latest).toBeNull()
  })

  it('converts the device and interface choices, and survives an empty answer', async () => {
    http.apiGet.mockResolvedValue({ devices: [{ hostname: 'sw', interfaces: [{ if_index: 2, name: 'eth0', speed_bps: null }] }] })
    expect(await getBandwidthChoices()).toEqual([{ hostname: 'sw', interfaces: [{ ifIndex: 2, name: 'eth0', speedBps: null }] }])

    http.apiGet.mockResolvedValue(null)
    expect(await getBandwidthChoices()).toEqual([])
  })

  it('reads, refreshes and changes the interfaces of a device', async () => {
    const body = { device: { id: 4, nagios_host_name: 'sw' }, snmp: true, max_monitored: 16, interfaces: [] }
    http.apiGet.mockResolvedValue(body)
    http.apiPost.mockResolvedValue(body)
    http.apiPut.mockResolvedValue({ ...body, config_ok: true })

    expect(await getDeviceInterfaces(4)).toEqual(body)
    expect(http.apiGet).toHaveBeenCalledWith('/api/system/hosts/4/interfaces')
    await refreshDeviceInterfaces(4)
    expect(http.apiPost).toHaveBeenCalledWith('/api/system/hosts/4/interfaces/refresh')
    await setInterfaceMonitored(4, 2, true)
    expect(http.apiPut).toHaveBeenCalledWith('/api/system/hosts/4/interfaces/2', { monitored: true })
  })

  it('treats an answer without a list as a device with no interfaces', async () => {
    http.apiGet.mockResolvedValue({ hostname: 'web-01' })
    expect(await getDeviceInterfaces(4)).toMatchObject({ snmp: false, interfaces: [] })
  })
})
