import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { HostAvailabilityReportTable } from '../components/reports/HostAvailabilityReportTable'
import { fromHostAvailabilityResponse } from '../types/report'

vi.mock('../contexts/SystemSettingsContext', () => ({ useSystemSettings: () => ({ settings: {
  exportFormats: ['CSV', 'XLS', 'PDF'], dateTimeFormat: 'YYYY-MM-DD', timeZone: 'UTC+00:00',
} }) }))

// Host Availability shows the host's current state, last check and last state change (#228).
const row = (overrides = {}) => ({ hostname: 'web-01', state: 'Up' as string | null, uptimePct: 80, totalSnapshots: 100,
  lastCheck: '2026-10-18T15:59:00+00:00', lastStateChange: '2026-10-17T09:00:00+00:00', ...overrides })
const available = { available: true, observed_at: '2026-10-18T16:00:00+00:00', notice: null }
const unavailable = { available: false, observed_at: null,
  notice: 'Current status unavailable. Historical availability is still shown; retry the report to refresh status.' }

describe('host availability current state', () => {
  it('shows each host state and its last check and last state change', () => {
    render(<HostAvailabilityReportTable hosts={[row(), row({ hostname: 'db-01', state: 'Down' })]} isLoading={false} currentStatus={available} />)
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Down')).toBeInTheDocument()
    expect(screen.queryByText('Unknown')).not.toBeInTheDocument()
    const web = screen.getByRole('row', { name: /web-01/ })
    expect(within(web).getByText(/2026-10-18/)).toBeInTheDocument()   // last check
    expect(within(web).getByText(/2026-10-17/)).toBeInTheDocument()   // last state change
    expect(within(web).queryByText('—')).not.toBeInTheDocument()
  })

  it('shows a dash, not a red badge, for a host with no current state', () => {
    render(<HostAvailabilityReportTable hosts={[row({ state: null, lastCheck: null, lastStateChange: null })]} isLoading={false} currentStatus={unavailable} />)
    const web = screen.getByRole('row', { name: /web-01/ })
    expect(within(web).queryByText('Unknown')).not.toBeInTheDocument()
    expect(within(web).queryByText('Down')).not.toBeInTheDocument()
    expect(within(web).getAllByText('—').length).toBeGreaterThanOrEqual(1)
  })

  it('says why when current status could not be read, and not otherwise', () => {
    const { rerender } = render(<HostAvailabilityReportTable hosts={[row({ state: null })]} isLoading={false} currentStatus={unavailable} />)
    expect(screen.getByText(/Current status unavailable/)).toBeInTheDocument()
    rerender(<HostAvailabilityReportTable hosts={[row()]} isLoading={false} currentStatus={available} />)
    expect(screen.queryByText(/Current status unavailable/)).not.toBeInTheDocument()
  })

  it('maps the response, keeping a null state and the current-status context', () => {
    const report = fromHostAvailabilityResponse({
      period: { period: 'last_24h', start: '2026-10-17T16:00:00+00:00', end: '2026-10-18T16:00:00+00:00' },
      summary: { total: 1, up: 0, down: 0, unreachable: 0, uptime_pct: 80 },
      current_status: unavailable,
      hosts: [{ hostname: 'web-01', state: null, uptime_pct: 80, total_snapshots: 100, last_check: null, last_state_change: null }],
    })
    expect(report.hosts[0].state).toBeNull()
    expect(report.currentStatus).toEqual(unavailable)
  })
})
