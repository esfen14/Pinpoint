import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ServiceRecoverySection } from '../components/device-inventory/ServiceRecoverySection'
import { ServiceStatusTable } from '../components/system-status/ServiceStatusTable'
import { ApiError } from '../lib/api'
import { recoveryKey, type ServiceRecovery } from '../types/remediation'
import type { ServiceRow } from '../types/service'

const api = vi.hoisted(() => ({ getServiceRecovery: vi.fn(), saveServiceRecovery: vi.fn() }))
vi.mock('../lib/remediationApi', () => ({
  getServiceRecovery: (host: string, service: string) => api.getServiceRecovery(host, service),
  saveServiceRecovery: (host: string, service: string, input: unknown) =>
    api.saveServiceRecovery(host, service, input),
}))

const permissions = vi.hoisted(() => ({ granted: new Set<string>() }))
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: null, isLoading: false, hasPermission: (name: string) => permissions.granted.has(name) }),
}))

const OFF: ServiceRecovery = {
  hostname: 'web-01',
  service: 'ssh-22-tcp',
  enabled: false,
  maxRestartsPerHour: 2,
  version: null,
  actionId: null,
  actionType: 'restart_remote_service',
  unit: 'ssh',
  canEnable: true,
  reason: null,
  otherActions: [],
  lastRun: null,
}
const ON: ServiceRecovery = { ...OFF, enabled: true, maxRestartsPerHour: 3, version: 1, actionId: 9 }

function mount() {
  render(
    <MemoryRouter>
      <ServiceRecoverySection hostname="web-01" service="ssh-22-tcp" />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  api.getServiceRecovery.mockReset().mockResolvedValue(OFF)
  api.saveServiceRecovery.mockReset().mockResolvedValue(ON)
  permissions.granted = new Set(['remediation.view', 'remediation.manage'])
})

describe('ServiceRecoverySection', () => {
  it('shows nothing and asks for nothing without remediation.view', () => {
    permissions.granted = new Set(['system.hosts'])
    mount()

    expect(screen.queryByText('Recover automatically')).not.toBeInTheDocument()
    expect(api.getServiceRecovery).not.toHaveBeenCalled()
  })

  it('loads the setting for the service and shows the switch off with the default limit', async () => {
    mount()

    expect(screen.getByText(/Loading recovery setting/)).toBeInTheDocument()
    const toggle = await screen.findByRole('switch', { name: 'Recover automatically' })
    expect(api.getServiceRecovery).toHaveBeenCalledWith('web-01', 'ssh-22-tcp')
    expect(toggle).not.toBeChecked()
    expect(toggle).toBeEnabled()
    expect(screen.getByLabelText('Restarts per hour')).toHaveValue(2)
  })

  it('warns that switching on makes the system restart the service on its own', async () => {
    mount()
    await userEvent.click(await screen.findByRole('switch', { name: 'Recover automatically' }))

    expect(screen.getByRole('note')).toHaveTextContent(/restart ssh on its own/)
    expect(screen.getByRole('note')).toHaveTextContent(/2 times an hour/)
  })

  it('saves the switch and the limit, with the version, and shows what the server returned', async () => {
    api.getServiceRecovery.mockResolvedValue(ON)
    api.saveServiceRecovery.mockResolvedValue({ ...ON, maxRestartsPerHour: 5, version: 2 })
    mount()
    await screen.findByRole('switch', { name: 'Recover automatically' })

    const limit = screen.getByLabelText('Restarts per hour')
    await userEvent.clear(limit)
    await userEvent.type(limit, '5')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(api.saveServiceRecovery).toHaveBeenCalledWith('web-01', 'ssh-22-tcp', {
        enabled: true,
        maxRestartsPerHour: 5,
        version: 1,
      }),
    )
    expect(await screen.findByText('Saved.')).toBeInTheDocument()
    expect(screen.getByLabelText('Restarts per hour')).toHaveValue(5)
  })

  it('sends no version for a setting that does not exist yet', async () => {
    mount()
    await userEvent.click(await screen.findByRole('switch', { name: 'Recover automatically' }))
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(api.saveServiceRecovery).toHaveBeenCalledWith('web-01', 'ssh-22-tcp', {
        enabled: true,
        maxRestartsPerHour: 2,
        version: null,
      }),
    )
  })

  it.each(['0', '7', '', '2.5'])('does not save a limit of "%s"', async (value) => {
    api.getServiceRecovery.mockResolvedValue(ON)
    mount()
    await screen.findByRole('switch', { name: 'Recover automatically' })

    const limit = screen.getByLabelText('Restarts per hour')
    await userEvent.clear(limit)
    if (value) await userEvent.type(limit, value)

    expect(screen.getByText(/whole number from 1 to 6/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
    expect(api.saveServiceRecovery).not.toHaveBeenCalled()
  })

  it('disables the switch and shows the reason when no valid action exists', async () => {
    api.getServiceRecovery.mockResolvedValue({
      ...OFF,
      canEnable: false,
      reason: 'Monitoring of the device is paused.',
      actionType: null,
      unit: null,
    })
    mount()

    const toggle = await screen.findByRole('switch', { name: 'Recover automatically' })
    expect(toggle).toBeDisabled()
    expect(screen.getByText('Monitoring of the device is paused.')).toBeInTheDocument()
  })

  it('still lets an enabled setting be switched off when it can no longer be enabled', async () => {
    api.getServiceRecovery.mockResolvedValue({ ...ON, canEnable: false, reason: 'Monitoring of the device is paused.' })
    mount()

    const toggle = await screen.findByRole('switch', { name: 'Recover automatically' })
    expect(toggle).toBeEnabled()
    await userEvent.click(toggle)
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled()
  })

  it('is read only with remediation.view alone', async () => {
    permissions.granted = new Set(['remediation.view'])
    api.getServiceRecovery.mockResolvedValue(ON)
    mount()

    expect(await screen.findByRole('switch', { name: 'Recover automatically' })).toBeDisabled()
    expect(screen.getByLabelText('Restarts per hour')).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument()
    expect(screen.getByText(/You can see this setting but not change it/)).toBeInTheDocument()
  })

  it('shows the last result with a link to the Remediation page', async () => {
    api.getServiceRecovery.mockResolvedValue({
      ...ON,
      lastRun: {
        id: 41, actionId: 9, actionName: 'x', hostname: 'web-01', service: 'ssh-22-tcp', state: 'CRITICAL',
        stateType: 'HARD', attempt: 3, receivedAt: '2026-10-17T11:00:00+00:00', startedAt: null, finishedAt: null,
        outcome: 'succeeded', reason: null,
      },
    })
    mount()

    expect(await screen.findByText(/Last result: Succeeded/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'View in Remediation' })).toHaveAttribute('href', '/remediation')
  })

  it('names other automatic actions that also cover the service', async () => {
    api.getServiceRecovery.mockResolvedValue({ ...OFF, otherActions: [{ id: 2, name: 'all-ssh' }] })
    mount()

    expect(await screen.findByText(/Other automatic actions also cover this service: all-ssh/)).toBeInTheDocument()
  })

  it('shows an error with a retry when the setting cannot be loaded', async () => {
    api.getServiceRecovery.mockRejectedValueOnce(new ApiError('boom', 500)).mockResolvedValue(OFF)
    mount()

    expect(await screen.findByRole('alert')).toHaveTextContent('boom')
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('switch', { name: 'Recover automatically' })).toBeInTheDocument()
  })

  it('explains a 403 on load', async () => {
    api.getServiceRecovery.mockRejectedValue(new ApiError('Forbidden', 403))
    mount()

    expect(await screen.findByRole('alert')).toHaveTextContent(/do not have permission/)
  })

  it('offers a reload after a 409 and loads the newer version', async () => {
    api.getServiceRecovery.mockResolvedValueOnce(ON).mockResolvedValue({ ...ON, version: 2, maxRestartsPerHour: 6 })
    api.saveServiceRecovery.mockRejectedValue(new ApiError('changed', 409))
    mount()
    await userEvent.click(await screen.findByRole('switch', { name: 'Recover automatically' }))
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/changed by someone else/)
    await userEvent.click(screen.getByRole('button', { name: 'Reload' }))
    await waitFor(() => expect(screen.getByLabelText('Restarts per hour')).toHaveValue(6))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('shows the server message when saving is refused', async () => {
    api.saveServiceRecovery.mockRejectedValue(new ApiError('The setting could not be applied: bad config', 422))
    mount()
    await userEvent.click(await screen.findByRole('switch', { name: 'Recover automatically' }))
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The setting could not be applied: bad config')
    expect(screen.getByRole('switch', { name: 'Recover automatically' })).toBeChecked()
  })
})

function serviceRow(hostname: string, service: string): ServiceRow {
  return {
    hostname, service, state: 'OK', stateType: 'HARD', lastCheck: '2026-10-17T11:59:00+00:00', checkLatency: 0.01,
    pluginOutput: 'OK', isFlapping: false, inDowntime: false, nagiosAck: 'none', ack: null,
  }
}

function table(autoRecovery?: ReadonlySet<string>) {
  render(
    <MemoryRouter>
      <ServiceStatusTable
        services={[serviceRow('web-01', 'ssh-22-tcp'), serviceRow('web-01', 'http-80-tcp')]}
        isLoading={false}
        query=""
        onQueryChange={vi.fn()}
        stateFilter="All"
        onStateFilterChange={vi.fn()}
        showFilter={false}
        onToggleFilter={vi.fn()}
        sortAsc
        onToggleSort={vi.fn()}
        page={1}
        pageCount={1}
        total={2}
        hasNext={false}
        hasPrev={false}
        onPageChange={vi.fn()}
        onAcknowledge={vi.fn()}
        onUnacknowledge={vi.fn()}
        autoRecovery={autoRecovery}
      />
    </MemoryRouter>,
  )
}

describe('System Status service row', () => {
  it('marks only the services that recover automatically, with a link to the Remediation page', () => {
    table(new Set([recoveryKey('web-01', 'ssh-22-tcp')]))

    const links = screen.getAllByRole('link', { name: /Recovers automatically/ })
    expect(links).toHaveLength(1)
    expect(links[0]).toHaveAttribute('href', '/remediation')
  })

  it('shows no mark when the page supplies none', () => {
    table()

    expect(screen.queryByRole('link', { name: /Recovers automatically/ })).not.toBeInTheDocument()
  })
})
