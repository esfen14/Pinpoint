import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { SystemStatusPage } from '../pages/SystemStatusPage'

vi.mock('../contexts/SystemSettingsContext', () => ({
  useSystemSettings: () => ({ settings: { theme: 'dark' } }),
}))

// The last-recovery badge asks whether the user may view remediation; these tests are about the table, so they have no permissions.
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: { permissions: [] }, isLoading: false, hasPermission: () => false }),
}))

const apiGet = vi.fn()

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return {
    ...actual,
    apiGet: (path: string) => apiGet(path),
    apiPost: vi.fn(),
    apiDelete: vi.fn(),
  }
})

function service(hostname: string, name: string, isFlapping: boolean) {
  return {
    hostname,
    service: name,
    state: 'OK',
    state_type: 'HARD',
    last_check: '2026-09-26T10:00:00+00:00',
    check_latency: 0.01,
    plugin_output: 'OK',
    is_flapping: isFlapping,
    in_downtime: false,
    nagios_ack: 'none',
    ack: null,
  }
}

function listResponse(items: unknown[]) {
  return { items, page: 1, per_page: 10, pages: 1, total: items.length, has_next: false, has_prev: false }
}

function route(path: string) {
  if (path.startsWith('/api/system/dashboard/summary')) {
    return Promise.resolve({ services: { total: 0, ok: 0, warning: 0, critical: 0, unknown: 0 } })
  }
  const params = new URLSearchParams(path.split('?')[1])
  const all = [service('web-1', 'http-80-TCP', false), service('web-1', 'ssh-22-TCP', true)]
  return Promise.resolve(listResponse(params.get('flapping') === 'true' ? all.filter((s) => s.is_flapping) : all))
}

function listCalls() {
  return apiGet.mock.calls
    .map(([path]) => String(path))
    .filter((path) => path.startsWith('/api/system/network-health/services?'))
    .map((path) => new URLSearchParams(path.split('?')[1]))
}

describe('SystemStatusPage flapping filter', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiGet.mockImplementation(route)
  })

  it('lists only flapping services from the server, then all again', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><SystemStatusPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('http-80-TCP')).toBeInTheDocument())
    expect(listCalls()[0].has('flapping')).toBe(false)

    await user.click(screen.getByRole('button', { name: 'Filter' }))
    await user.click(screen.getByRole('button', { name: 'Flapping only' }))
    await waitFor(() => expect(listCalls().at(-1)?.get('flapping')).toBe('true'))
    await waitFor(() => expect(screen.queryByText('http-80-TCP')).not.toBeInTheDocument())
    expect(screen.getByText('ssh-22-TCP')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Filter' }))
    await user.click(screen.getByRole('button', { name: 'Flapping only' }))
    await waitFor(() => expect(screen.getByText('http-80-TCP')).toBeInTheDocument())
    expect(listCalls().at(-1)?.has('flapping')).toBe(false)
  })
})
