import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { DeviceInterfacesSection } from '../components/device-inventory/DeviceInterfacesSection'
import type { DeviceInterface, DeviceInterfacesResponse } from '../types/bandwidth'

const api = vi.hoisted(() => ({
  getDeviceInterfaces: vi.fn(), refreshDeviceInterfaces: vi.fn(), setInterfaceMonitored: vi.fn(),
}))
vi.mock('../lib/bandwidthApi', () => api)

const permissions = vi.hoisted(() => ({ granted: new Set<string>() }))
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: null, isLoading: false, hasPermission: (name: string) => permissions.granted.has(name) }),
}))

const iface = (overrides: Partial<DeviceInterface> = {}): DeviceInterface => ({
  if_index: 2, name: 'eth0', speed_bps: 1_000_000_000, admin_status: 'up', oper_status: 'up',
  monitored: false, present: true, last_seen_at: null, ...overrides,
})

const listing = (interfaces: DeviceInterface[], overrides: Partial<DeviceInterfacesResponse> = {}): DeviceInterfacesResponse => ({
  device: { id: 4, nagios_host_name: 'switch-a' }, snmp: true, max_monitored: 16, interfaces, ...overrides,
})

const applied = { config_applied: true, config_ok: true, config_message: 'applied' }

function renderSection() {
  return render(<DeviceInterfacesSection deviceId={4} hostname="switch-a" />)
}

beforeEach(() => {
  api.getDeviceInterfaces.mockReset().mockResolvedValue(listing([iface(), iface({ if_index: 3, name: 'eth1', speed_bps: null })]))
  api.refreshDeviceInterfaces.mockReset().mockResolvedValue(listing([iface()]))
  api.setInterfaceMonitored.mockReset().mockImplementation(async (_id: number, index: number, monitored: boolean) => ({
    ...listing([iface({ monitored: index === 2 ? monitored : false }), iface({ if_index: 3, name: 'eth1', speed_bps: null })]),
    ...applied,
  }))
  permissions.granted = new Set(['system.hosts', 'system.hosts.edit'])
})

describe('states of the section', () => {
  it('shows a loading indicator first', () => {
    api.getDeviceInterfaces.mockReturnValue(new Promise(() => {}))
    renderSection()
    expect(screen.getByText('Loading interfaces…')).toBeInTheDocument()
  })

  it('shows the error with Retry, and Retry loads again', async () => {
    api.getDeviceInterfaces.mockRejectedValueOnce(new ApiError('Device not found.', 404))
    renderSection()

    expect(await screen.findByText('Device not found.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByText('eth0')).toBeInTheDocument()
  })

  it('invites a refresh when an SNMP device has no interfaces yet', async () => {
    api.getDeviceInterfaces.mockResolvedValue(listing([]))
    renderSection()

    expect(await screen.findByText(/No interfaces read from switch-a yet/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument()
  })

  it('is not shown at all for a device that does not answer SNMP', async () => {
    api.getDeviceInterfaces.mockResolvedValue(listing([], { snmp: false }))
    const { container } = renderSection()

    await waitFor(() => expect(screen.queryByText('Loading interfaces…')).not.toBeInTheDocument())
    expect(container).toBeEmptyDOMElement()
  })

  it('lists name, number, speed and status of every interface', async () => {
    renderSection()

    expect(await screen.findByText('eth0')).toBeInTheDocument()
    expect(screen.getByText('#2')).toBeInTheDocument()
    expect(screen.getByText('1.00 Gbit/s')).toBeInTheDocument()
    expect(screen.getAllByText('up').length).toBeGreaterThan(0)
    expect(screen.getByText('0 of 16 monitored. Each monitored interface adds an in and an out bandwidth check.')).toBeInTheDocument()
  })

  it('marks an interface the device no longer reports', async () => {
    api.getDeviceInterfaces.mockResolvedValue(listing([iface({ present: false, monitored: true })]))
    renderSection()

    expect(await screen.findByText('no longer reported by the device')).toBeInTheDocument()
  })
})

describe('turning monitoring on and off', () => {
  it('sends the new choice and shows the answer', async () => {
    renderSection()
    const box = await screen.findByRole('checkbox', { name: 'Monitor eth0' })
    expect(box).not.toBeChecked()

    fireEvent.click(box)

    await waitFor(() => expect(screen.getByRole('checkbox', { name: 'Monitor eth0' })).toBeChecked())
    expect(api.setInterfaceMonitored).toHaveBeenCalledWith(4, 2, true)
    expect(screen.getByText(/1 of 16 monitored/)).toBeInTheDocument()
  })

  it('can turn it off again', async () => {
    api.getDeviceInterfaces.mockResolvedValue(listing([iface({ monitored: true })]))
    renderSection()

    fireEvent.click(await screen.findByRole('checkbox', { name: 'Monitor eth0' }))

    await waitFor(() => expect(api.setInterfaceMonitored).toHaveBeenCalledWith(4, 2, false))
  })

  it('reports a change that was saved but is not in Nagios yet', async () => {
    api.setInterfaceMonitored.mockResolvedValue({
      ...listing([iface({ monitored: true })]), config_applied: false, config_ok: false, config_message: 'Config failed to validate',
    })
    renderSection()

    fireEvent.click(await screen.findByRole('checkbox', { name: 'Monitor eth0' }))

    expect(await screen.findByRole('status')).toHaveTextContent('The change was saved but Nagios was not updated: Config failed to validate')
  })

  it('shows the server error when the change is refused', async () => {
    api.setInterfaceMonitored.mockRejectedValue(new ApiError('At most 16 interfaces can be monitored on one device.', 400))
    renderSection()

    fireEvent.click(await screen.findByRole('checkbox', { name: 'Monitor eth0' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('At most 16 interfaces can be monitored on one device.')
  })

  it('does not allow more than the limit', async () => {
    api.getDeviceInterfaces.mockResolvedValue(listing([iface({ monitored: true }), iface({ if_index: 3, name: 'eth1' })], { max_monitored: 1 }))
    renderSection()

    expect(await screen.findByRole('checkbox', { name: 'Monitor eth1' })).toBeDisabled()
    expect(screen.getByRole('checkbox', { name: 'Monitor eth0' })).toBeEnabled()
  })

  it('is read-only without system.hosts.edit', async () => {
    permissions.granted = new Set(['system.hosts'])
    renderSection()

    expect(await screen.findByRole('checkbox', { name: 'Monitor eth0' })).toBeDisabled()
    expect(screen.getByText(/You can view interfaces but not change them/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Refresh' })).not.toBeInTheDocument()
  })
})

describe('refreshing from the device', () => {
  it('asks the device and replaces the list', async () => {
    renderSection()
    await screen.findByText('eth0')

    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }))

    await waitFor(() => expect(screen.queryByText('eth1')).not.toBeInTheDocument())
    expect(api.refreshDeviceInterfaces).toHaveBeenCalledWith(4)
  })

  it('shows why the device could not be read', async () => {
    api.refreshDeviceInterfaces.mockRejectedValue(new ApiError('The device did not answer in time.', 502))
    renderSection()
    await screen.findByText('eth0')

    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The device did not answer in time.')
    expect(screen.getByText('eth1')).toBeInTheDocument()       // the old list stays
  })

  it('shows progress while it waits', async () => {
    api.refreshDeviceInterfaces.mockReturnValue(new Promise(() => {}))
    renderSection()
    await screen.findByText('eth0')

    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }))

    expect(await screen.findByRole('button', { name: 'Refreshing…' })).toBeDisabled()
  })
})
