import { render, renderHook, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ServiceStatusTable } from '../components/system-status/ServiceStatusTable'
import { useLastRecoveries } from '../hooks/useLastRecoveries'
import { recoveryBadgeFor, type LastRun } from '../types/remediation'
import type { ServiceRow } from '../types/service'

const apiGet = vi.hoisted(() => vi.fn())
vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, apiGet }
})

let permissions: string[] = []
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({
    user: { permissions },
    isLoading: false,
    hasPermission: (name: string) => permissions.includes(name),
  }),
}))

function row(hostname: string, service: string): ServiceRow {
  return {
    hostname,
    service,
    state: 'OK',
    stateType: 'HARD',
    lastCheck: '2026-10-17T11:59:00+00:00',
    checkLatency: 0.01,
    pluginOutput: 'OK',
    isFlapping: false,
    inDowntime: false,
    nagiosAck: 'none',
    ack: null,
  }
}

function last(overrides: Partial<LastRun> = {}): LastRun {
  return {
    runId: 7, hostname: 'web-01', service: 'HTTP', outcome: 'succeeded', notifyState: null,
    receivedAt: '2026-10-17T11:00:00', ...overrides,
  }
}

function renderTable(recoveries?: LastRun[] | null) {
  return render(
    <MemoryRouter>
      <ServiceStatusTable
        services={[row('web-01', 'HTTP'), row('web-01', 'SSH')]}
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
        recoveries={recoveries}
      />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  permissions = ['remediation.view']
  apiGet.mockReset()
})

describe('recoveryBadgeFor', () => {
  it.each([
    ['succeeded', 'Auto-recovered'],
    ['failed', 'Recovery failed'],
    ['timed_out', 'Recovery failed'],
    ['skipped_cooldown', 'Recovery limited'],
    ['skipped_hourly_cap', 'Recovery limited'],
    ['skipped_kill_switch', 'Recovery skipped'],
    ['skipped_maintenance', 'Recovery skipped'],
    ['skipped_downtime', 'Recovery skipped'],
    ['skipped_acknowledged', 'Recovery skipped'],
    ['running', 'Recovering'],
    ['interrupted', 'Recovery interrupted'],
  ] as const)('labels %s as %s', (outcome, text) => {
    expect(recoveryBadgeFor(last({ outcome })).text).toBe(text)
  })

  it('says in the tooltip whether the operator was told', () => {
    expect(recoveryBadgeFor(last({ outcome: 'failed', notifyState: 'sent' })).title).toMatch(/operator was notified/i)
    expect(recoveryBadgeFor(last({ outcome: 'failed', notifyState: 'failed' })).title).toMatch(/notification failed/i)
    expect(recoveryBadgeFor(last({ outcome: 'succeeded' })).title).not.toMatch(/notif/i)
  })
})

describe('Service status table: last recovery badge', () => {
  it('shows the badge on the matching row and links to the run', () => {
    renderTable([last({ outcome: 'failed', notifyState: 'sent' })])
    const http = screen.getByText('HTTP').closest('tr') as HTMLElement
    const badge = within(http).getByRole('link', { name: /Recovery failed/ })
    expect(badge).toHaveAttribute('href', '/remediation?run=7')
    const ssh = screen.getByText('SSH').closest('tr') as HTMLElement
    expect(within(ssh).queryByRole('link')).not.toBeInTheDocument()
  })

  it('shows no badge without recoveries, while they load, or when they could not be loaded', () => {
    renderTable(undefined)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('shows no badge when the list is empty or null', () => {
    renderTable([])
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('matches a service by host and name together', () => {
    renderTable([last({ hostname: 'web-02' })])
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})

describe('useLastRecoveries', () => {
  it('loads the last runs for a user who may view remediation', async () => {
    apiGet.mockResolvedValue({ items: [last()] })
    const { result } = renderHook(() => useLastRecoveries())
    await waitFor(() => expect(result.current).toHaveLength(1))
    expect(apiGet).toHaveBeenCalledWith('/api/system/remediation/last-runs')
  })

  it('does not call the server without the remediation view permission', async () => {
    permissions = []
    const { result } = renderHook(() => useLastRecoveries())
    await Promise.resolve()
    expect(apiGet).not.toHaveBeenCalled()
    expect(result.current).toBeNull()
  })

  it('stays quiet when the request fails', async () => {
    apiGet.mockRejectedValue(new Error('boom'))
    const { result } = renderHook(() => useLastRecoveries())
    await waitFor(() => expect(apiGet).toHaveBeenCalled())
    expect(result.current).toBeNull()
  })
})
