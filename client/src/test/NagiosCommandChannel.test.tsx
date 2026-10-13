import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { StatusDetailDrawer } from '../components/device-inventory/StatusDetailDrawer'
import { ApiError } from '../lib/api'
import { nagiosSyncNotice } from '../types/nagiosSync'

const api = vi.hoisted(() => ({ apiGet: vi.fn(), apiPost: vi.fn(), apiDelete: vi.fn() }))
vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return {
    ...actual,
    apiGet: (path: string) => api.apiGet(path),
    apiPost: (path: string, body?: unknown) => api.apiPost(path, body),
    apiDelete: (path: string, body?: unknown) => api.apiDelete(path, body),
  }
})

const permissions = vi.hoisted(() => ({ granted: new Set<string>() }))
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: null, isLoading: false, hasPermission: (name: string) => permissions.granted.has(name) }),
}))

function detail(overrides: Record<string, unknown> = {}) {
  return {
    hostname: 'web-01',
    state: 'Critical',
    state_type: 'HARD',
    plugin_output: 'CRIT',
    last_check: null,
    check_latency: 0.01,
    check_execution_time: 0.05,
    is_flapping: false,
    in_downtime: false,
    nagios_ack: 'none',
    ack: null,
    perf_data: [],
    ...overrides,
  }
}

const HOST_RECHECK = '/api/system/network-health/hosts/web-01/recheck'

beforeEach(() => {
  api.apiGet.mockReset().mockResolvedValue(detail({ services: [{ service: 'cpu/percent', state: 'Critical', plugin_output: '', last_check: null }] }))
  api.apiPost.mockReset().mockResolvedValue({})
  api.apiDelete.mockReset().mockResolvedValue({})
  permissions.granted = new Set(['system.recheck', 'system.acknowledge_alerts'])
})

describe('nagiosSyncNotice', () => {
  it('is empty on success or when the response says nothing', () => {
    expect(nagiosSyncNotice({ nagios_synced: true, nagios_message: null })).toBeNull()
    expect(nagiosSyncNotice(undefined)).toBeNull()
    expect(nagiosSyncNotice({})).toBeNull()
  })

  it('uses the server message, or a default, when Nagios was not updated', () => {
    expect(nagiosSyncNotice({ nagios_synced: false, nagios_message: 'Pipe down.' })).toBe('Pipe down.')
    expect(nagiosSyncNotice({ nagios_synced: false })).toMatch(/Nagios was not updated/)
  })
})

describe('Check now button', () => {
  it('is hidden without system.recheck', async () => {
    permissions.granted = new Set()
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    await screen.findByRole('heading', { name: 'Timestamps' })
    expect(screen.queryByRole('button', { name: /Check now/ })).not.toBeInTheDocument()
  })

  it('requests a host re-check and starts a cooldown', async () => {
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    fireEvent.click(await screen.findByRole('button', { name: 'Check now' }))

    await waitFor(() => expect(api.apiPost).toHaveBeenCalledWith(HOST_RECHECK, undefined))
    expect(await screen.findByText(/Check requested/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Check now \(wait \d+s\)/ })).toBeDisabled()
  })

  it('requests a service re-check with slashes in the name kept as path segments', async () => {
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    fireEvent.click(await screen.findByRole('button', { name: /cpu\/percent/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Check now' }))

    await waitFor(() => expect(api.apiPost).toHaveBeenCalledWith(
      '/api/system/network-health/services/web-01/cpu/percent/recheck', undefined))
  })

  it('shows the server message and the wait when rate limited', async () => {
    api.apiPost.mockRejectedValue(new ApiError('A check was just requested. Try again in 7 seconds.', 429, { retry_after: 7 }))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    fireEvent.click(await screen.findByRole('button', { name: 'Check now' }))

    expect(await screen.findByText('A check was just requested. Try again in 7 seconds.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Check now (wait 7s)' })).toBeDisabled()
  })

  it('shows an error and stays usable when Nagios cannot be reached', async () => {
    api.apiPost.mockRejectedValue(new ApiError('Nagios could not be asked to re-check.', 503))
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    fireEvent.click(await screen.findByRole('button', { name: 'Check now' }))

    expect(await screen.findByText(/could not be asked/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Check now' })).toBeEnabled()
  })
})

describe('Nagios acknowledgement notice', () => {
  async function acknowledge() {
    render(<StatusDetailDrawer hostname="web-01" onClose={() => {}} />)
    fireEvent.click(await screen.findByRole('button', { name: /cpu\/percent/ }))
    fireEvent.change(await screen.findByLabelText('Acknowledgement comment'), { target: { value: 'on it' } })
    fireEvent.click(screen.getByRole('button', { name: 'Acknowledge' }))
  }

  it('is shown when the acknowledgement did not reach Nagios', async () => {
    api.apiPost.mockResolvedValue({ nagios_synced: false, nagios_message: 'Saved in PinPoint, but Nagios was not updated. Notifications may continue.' })
    await acknowledge()
    expect(await screen.findByRole('status')).toHaveTextContent('Nagios was not updated')
  })

  it('is not shown when Nagios was updated', async () => {
    api.apiPost.mockResolvedValue({ nagios_synced: true, nagios_message: null })
    await acknowledge()
    await waitFor(() => expect(api.apiPost).toHaveBeenCalled())
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
