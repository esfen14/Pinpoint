import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ExtraReports } from '../components/reports/ExtraReports'
import { HostAvailabilityReportTable } from '../components/reports/HostAvailabilityReportTable'
import { ReportsPage } from '../pages/ReportsPage'

const mocks = vi.hoisted(() => ({ get: vi.fn() }))
vi.mock('../lib/api', () => ({ apiGet: mocks.get, apiPost: vi.fn().mockResolvedValue({}), errorMessage: (e: Error) => e.message }))
vi.mock('../contexts/SystemSettingsContext', () => ({ useSystemSettings: () => ({ settings: {
  exportFormats: ['CSV', 'XLS', 'PDF'], dateTimeFormat: 'YYYY-MM-DD', timeZone: 'UTC+00:00',
} }) }))

// A period with no recorded host time must say so instead of looking like a measured result (#229).
const period = { period: 'custom', start: '2026-09-01T00:00:00+00:00', end: '2026-09-30T23:59:59+00:00' }
const available = { available: true, observed_at: '2026-10-18T16:00:00+00:00', notice: null }   // the API body's current_status (#228), ignored here
const row = (overrides = {}) => ({ hostname: 'web-01', state: 'Up', uptimePct: null as number | null, totalSnapshots: 0,
  lastCheck: null, lastStateChange: null, ...overrides })
const NOTICE = /No data in this period/

beforeEach(() => { vi.clearAllMocks() })

describe('host availability with no recorded time', () => {
  it('says there is no data when no host has recorded time', () => {
    render(<HostAvailabilityReportTable hosts={[row(), row({ hostname: 'db-01' })]} isLoading={false} />)
    expect(screen.getByRole('status')).toHaveTextContent(NOTICE)
    expect(screen.getByText('web-01')).toBeInTheDocument()   // the hosts asked about stay listed
  })

  it('does not say so when any host has recorded time, while loading, or for an empty list', () => {
    const { rerender } = render(<HostAvailabilityReportTable hosts={[row(), row({ hostname: 'db-01', uptimePct: 80, totalSnapshots: 100 })]} isLoading={false} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    rerender(<HostAvailabilityReportTable hosts={[row()]} isLoading />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    rerender(<HostAvailabilityReportTable hosts={[]} isLoading={false} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByText(NOTICE)).toBeInTheDocument()   // the existing empty-list row text
  })
})

describe('reports page with no recorded time', () => {
  const body = (hosts: object[]) => ({ period, current_status: available,
    summary: { total: hosts.length, up: 0, down: 0, unreachable: 0, uptime_pct: null }, hosts })
  const apiRow = (o = {}) => ({ hostname: 'web-01', state: 'Up', uptime_pct: null, total_snapshots: 0, last_check: null, last_state_change: null, ...o })

  it('shows the no-data message and not "Report generated successfully." when nothing was recorded', async () => {
    mocks.get.mockResolvedValue(body([apiRow(), apiRow({ hostname: 'db-01' })]))
    render(<ReportsPage />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run Report' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: 'Run Report' }))
    await screen.findByRole('status')
    expect(screen.getByRole('status')).toHaveTextContent(NOTICE)
    expect(screen.queryByText('Report generated successfully.')).not.toBeInTheDocument()
  })

  it('still says "Report generated successfully." when a host has recorded time', async () => {
    mocks.get.mockResolvedValue(body([apiRow({ uptime_pct: 80, total_snapshots: 100 })]))
    render(<ReportsPage />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run Report' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: 'Run Report' }))
    expect(await screen.findByText('Report generated successfully.')).toBeInTheDocument()
  })
})

describe('hosts by os with no recorded time', () => {
  const byOs = (uptime: number | null) => ({ period, current_status: available, summary: {}, by_os: [{ os_type: 'Linux', hosts: [
    { hostname: 'web-01', state: 'Up', uptime_pct: uptime, last_check: null, last_state_change: null }] }] })

  it('says there is no data when no host has an uptime', async () => {
    mocks.get.mockResolvedValue(byOs(null))
    render(<ExtraReports view="hosts-by-os" query="period=last_24h" runKey={0} onStatus={vi.fn()} onCards={vi.fn()} />)
    expect(await screen.findByRole('status')).toHaveTextContent(NOTICE)
    expect(screen.getByText('web-01')).toBeInTheDocument()
  })

  it('does not say so when a host has an uptime', async () => {
    mocks.get.mockResolvedValue(byOs(80))
    render(<ExtraReports view="hosts-by-os" query="period=last_24h" runKey={0} onStatus={vi.fn()} onCards={vi.fn()} />)
    await screen.findByText('web-01')
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
