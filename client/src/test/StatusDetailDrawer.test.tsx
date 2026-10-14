import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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

// The section has its own tests; here it only shows that it was rendered, and for which device.
vi.mock('../components/device-inventory/DevicePortsSection', () => ({
  DevicePortsSection: ({ deviceId, hostname }: { deviceId: number; hostname: string }) => (
    <div>Ports section for device {deviceId} ({hostname})</div>
  ),
}))

function detail(overrides: Record<string, unknown> = {}) {
  return {
    hostname: 'web-01',
    device_id: 4,
    state: 'Up',
    state_type: 'HARD',
    plugin_output: 'PING OK',
    last_check: '2026-10-05T09:30:00+00:00',
    check_latency: 0.012,
    check_execution_time: 0.05,
    is_flapping: false,
    in_downtime: false,
    nagios_ack: 'none',
    ack: null,
    perf_data: [],
    services: [{ service: 'ssh-22-tcp', state: 'Ok', plugin_output: 'SSH OK', last_check: null }],
    ...overrides,
  }
}

beforeEach(() => {
  api.apiGet.mockReset().mockResolvedValue(detail())
  permissions.granted = new Set(['system.hosts', 'system.network_health'])
})

describe('StatusDetailDrawer Ports section', () => {
  it('shows the Ports section for a discovered device the user may view', async () => {
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)

    expect(await screen.findByText('Ports section for device 4 (web-01)')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Services' })).toBeInTheDocument()       // existing sections are unchanged
    expect(screen.getByRole('heading', { name: 'Timestamps' })).toBeInTheDocument()
  })

  it('is shown after the services list', async () => {
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)

    const ports = await screen.findByText(/Ports section/)
    const services = screen.getByRole('heading', { name: 'Services' })
    expect(services.compareDocumentPosition(ports) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it.each([[null], [undefined]])('is not shown when the host has no device record (%s)', async (deviceId) => {
    api.apiGet.mockResolvedValue(detail({ device_id: deviceId }))
    render(<StatusDetailDrawer hostname="localhost" onClose={() => {}} />)

    await screen.findByRole('heading', { name: 'Timestamps' })
    expect(screen.queryByText(/Ports section/)).not.toBeInTheDocument()
  })

  it('is not shown without system.hosts', async () => {
    permissions.granted = new Set(['system.network_health'])
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)

    await screen.findByRole('heading', { name: 'Timestamps' })
    expect(screen.queryByText(/Ports section/)).not.toBeInTheDocument()
  })

  it('is not shown inside a service\'s own view', async () => {
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    await screen.findByText(/Ports section/)
    api.apiGet.mockResolvedValue(detail({ service: 'ssh-22-tcp', services: undefined }))

    fireEvent.click(screen.getByRole('button', { name: /ssh-22-tcp/ }))

    await screen.findByText('web-01 / ssh-22-tcp')
    expect(screen.queryByText(/Ports section/)).not.toBeInTheDocument()
  })

  it('asks for the host detail by host name as before', async () => {
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    await screen.findByText(/Ports section/)
    expect(api.apiGet).toHaveBeenCalledWith('/api/system/network-health/hosts/web-01/detail')
  })
})


describe('StatusDetailDrawer flap history', () => {
  function flapResponse(items: unknown[], globalEnabled: boolean | null = true) {
    return { hours: 24, global_flap_detection_enabled: globalEnabled, items }
  }

  function flapItem(overrides: Record<string, unknown> = {}) {
    return {
      type: 'host',
      hostname: 'web-01',
      service: null,
      snapshots_flagged: 7,
      first_flagged: '2026-10-05T08:00:00+00:00',
      last_flagged: '2026-10-05T09:00:00+00:00',
      currently_flapping: true,
      current_state: 'up',
      ...overrides,
    }
  }

  function serve(flap: unknown) {
    api.apiGet.mockImplementation((path: string) =>
      Promise.resolve(path.startsWith('/api/system/network-health/flapping') ? flap : detail()))
  }

  const flapCalls = () => api.apiGet.mock.calls.map(([path]) => String(path)).filter((p) => p.includes('/flapping'))

  it('lists how often the host was flagged in the chosen window', async () => {
    serve(flapResponse([flapItem(), flapItem({ hostname: 'other', snapshots_flagged: 99 })]))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)

    expect(await screen.findByRole('heading', { name: 'Flap history' })).toBeInTheDocument()
    expect(await screen.findByText(/Flagged as flapping in 7 checks/)).toBeInTheDocument()
    expect(screen.getByText(/Flapping now/)).toBeInTheDocument()
    expect(screen.queryByText(/99/)).not.toBeInTheDocument()
    expect(flapCalls()[0]).toBe('/api/system/network-health/flapping?hours=24')
  })

  it('asks again when the window changes', async () => {
    serve(flapResponse([flapItem()]))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    await screen.findByText(/Flagged as flapping in 7 checks/)

    fireEvent.change(screen.getByLabelText('Flap history window'), { target: { value: '168' } })

    await waitFor(() => expect(flapCalls().at(-1)).toBe('/api/system/network-health/flapping?hours=168'))
  })

  it('shows an empty state when it has not flapped', async () => {
    serve(flapResponse([flapItem({ hostname: 'other' })]))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)

    expect(await screen.findByText(/Not flagged as flapping/)).toBeInTheDocument()
  })

  it('shows an error when the history cannot be loaded', async () => {
    api.apiGet.mockImplementation((path: string) =>
      path.includes('/flapping') ? Promise.reject(new Error('boom')) : Promise.resolve(detail()))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)

    expect(await screen.findByText(/boom/)).toBeInTheDocument()
  })

  it('warns when Nagios has flap detection switched off globally', async () => {
    serve(flapResponse([], false))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)

    expect(await screen.findByText(/switched off in Nagios/i)).toBeInTheDocument()
  })

  it('does not warn when flap detection is on', async () => {
    serve(flapResponse([flapItem()], true))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    await screen.findByText(/Flagged as flapping/)

    expect(screen.queryByText(/switched off in Nagios/i)).not.toBeInTheDocument()
  })

  it('is left out without the network health permission', async () => {
    permissions.granted = new Set(['system.hosts'])
    serve(flapResponse([flapItem()]))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)

    await screen.findByRole('heading', { name: 'Timestamps' })
    expect(screen.queryByRole('heading', { name: 'Flap history' })).not.toBeInTheDocument()
    expect(flapCalls()).toHaveLength(0)
  })
})
