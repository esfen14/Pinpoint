import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { StatusDetailDrawer } from '../components/device-inventory/StatusDetailDrawer'

const api = vi.hoisted(() => ({ apiGet: vi.fn() }))
vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, apiGet: (path: string) => api.apiGet(path), apiPost: vi.fn(), apiDelete: vi.fn() }
})

const permissions = vi.hoisted(() => ({ granted: new Set<string>() }))
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: null, isLoading: false, hasPermission: (name: string) => permissions.granted.has(name) }),
}))

// The section has its own tests; here it only shows that the drawer rendered it, and for which device.
vi.mock('../components/device-inventory/DeviceSnmpSection', () => ({
  DeviceSnmpSection: ({ deviceId, hostname }: { deviceId: number; hostname: string }) => (
    <div>SNMP section for device {deviceId} ({hostname})</div>
  ),
}))
vi.mock('../components/device-inventory/DevicePortsSection', () => ({ DevicePortsSection: () => null }))
vi.mock('../components/device-inventory/DeviceInterfacesSection', () => ({ DeviceInterfacesSection: () => null }))

const detail = (overrides: Record<string, unknown> = {}) => ({
  hostname: 'web-01', device_id: 4, state: 'Up', state_type: 'HARD', plugin_output: 'PING OK',
  check_latency: 0.012, check_execution_time: 0.05, is_flapping: false, in_downtime: false, nagios_ack: 'none',
  ack: null, perf_data: [], services: [], ...overrides,
})

beforeEach(() => {
  api.apiGet.mockReset().mockResolvedValue(detail())
  permissions.granted = new Set(['system.hosts'])
})

describe('StatusDetailDrawer SNMP section', () => {
  it('shows the SNMP section for a discovered device the user may view', async () => {
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    expect(await screen.findByText('SNMP section for device 4 (web-01)')).toBeInTheDocument()
  })

  it('hides it without system.hosts', async () => {
    permissions.granted = new Set()
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    await screen.findByText('PING OK')
    expect(screen.queryByText(/SNMP section/)).not.toBeInTheDocument()
  })

  it('hides it for a host with no device record', async () => {
    api.apiGet.mockResolvedValue(detail({ device_id: null }))
    render(<StatusDetailDrawer hostname="localhost" onClose={() => {}} />)
    await screen.findByText('PING OK')
    expect(screen.queryByText(/SNMP section/)).not.toBeInTheDocument()
  })
})
