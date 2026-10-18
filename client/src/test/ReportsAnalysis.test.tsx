import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AvailabilityDetailDrawer } from '../components/reports/AvailabilityDetailDrawer'
import { AlertHistogramReport, AlertSummaryReport } from '../components/reports/AlertAnalysisReports'
import { HostAvailabilityReportTable } from '../components/reports/HostAvailabilityReportTable'
import { ReportsPage } from '../pages/ReportsPage'
import { exportMeta, formatDuration } from '../lib/reportFormat'
import type { AlertHistogram, AlertSummary, AvailabilityDetail } from '../types/report'

const mocks = vi.hoisted(() => ({ get: vi.fn(), export: vi.fn(), permissions: ['system.history'] as string[] }))
vi.mock('../lib/api', () => ({ apiGet: mocks.get, apiPost: vi.fn().mockResolvedValue({}), errorMessage: (e: Error) => e.message }))
vi.mock('../utils/exportData', () => ({ exportRows: mocks.export }))
vi.mock('../contexts/CurrentUserContext', () => ({ useCurrentUser: () => ({ hasPermission: (p: string) => mocks.permissions.includes(p) }) }))
vi.mock('../contexts/SystemSettingsContext', () => ({ useSystemSettings: () => ({ settings: {
  exportFormats: ['CSV', 'PDF'], dateTimeFormat: 'YYYY-MM-DD HH:mm:ss', timeZone: 'UTC',
} }) }))

const period = { period: 'last_24h', start: '2024-01-01T00:00:00', end: '2024-01-02T00:00:00', time_zone: { name: 'UTC', utc_offset_seconds: 0 } }
const T0 = 1_704_067_200

function detail(over: Partial<AvailabilityDetail> = {}): AvailabilityDetail {
  return {
    period, source: 'Nagios archive', generated_at: '2024-01-02T00:00:01+00:00',
    object: { hostname: 'web-01', service: null },
    totals: {
      window_seconds: 1000, known_seconds: 700, no_recorded_data_seconds: 300, no_data_seconds: 300,
      nagios_not_running_seconds: 0, unaccounted_seconds: 0,
      states: [
        { state: 'up', seconds: 400, scheduled_seconds: 100, unscheduled_seconds: 300, pct_of_total: 40, pct_of_known: 57.14 },
        { state: 'down', seconds: 300, scheduled_seconds: 0, unscheduled_seconds: 300, pct_of_total: 30, pct_of_known: 42.86 },
        { state: 'unreachable', seconds: 0, scheduled_seconds: 0, unscheduled_seconds: 0, pct_of_total: 0, pct_of_known: null },
      ],
    },
    complete: true, intervals_available: true, reconciliation: { matches: true, tolerance_seconds: 2, differences: {} }, notice: null,
    intervals: [
      { start: T0, end: T0 + 300, duration_seconds: 300, state: 'no_data', information: 'No recorded state', clipped_start: false, unknown_onset: true, continuing: false },
      { start: T0 + 300, end: T0 + 700, duration_seconds: 400, state: 'up', information: 'PING OK', clipped_start: true, unknown_onset: false, continuing: false },
      { start: T0 + 700, end: T0 + 1000, duration_seconds: 300, state: 'down', information: 'PING CRITICAL', clipped_start: false, unknown_onset: false, continuing: true },
    ],
    ...over,
  }
}

function renderDrawer(onClose = vi.fn()) {
  return render(<MemoryRouter><AvailabilityDetailDrawer hostname="web-01" service={null} query="period=last_24h" onClose={onClose} /></MemoryRouter>)
}

beforeEach(() => { vi.clearAllMocks(); mocks.permissions = ['system.history'] })

describe('availability detail drawer', () => {
  it('shows durations with both denominators, scheduled split, coverage and the accessible timeline table', async () => {
    mocks.get.mockResolvedValue(detail())
    renderDrawer()
    expect(await screen.findByText('State durations')).toBeInTheDocument()
    expect(mocks.get).toHaveBeenCalledWith('/api/system/report/availability-detail?period=last_24h&hostname=web-01')
    const table = screen.getAllByRole('table')[0]
    expect(within(table).getByText('57.14%')).toBeInTheDocument()
    expect(within(table).getByText('40%')).toBeInTheDocument()
    expect(within(table).getByText('—')).toBeInTheDocument()   // zero known denominator of Unreachable
    expect(screen.getByText(/Scheduled time \(maintenance\) is a part of each state/)).toBeInTheDocument()
    expect(screen.getByText('began before this period')).toBeInTheDocument()
    expect(screen.getByText('onset unknown')).toBeInTheDocument()
    expect(screen.getAllByText('continuing').length).toBeGreaterThan(0)
    expect(screen.getByText('PING CRITICAL')).toBeInTheDocument()
    // Every segment is reachable without a pointer and carries text, not colour alone.
    const segments = screen.getAllByRole('button', { name: /^(No recorded data|Up|Down),/ })
    expect(segments).toHaveLength(3)
  })

  it('withholds intervals and says why when they do not agree with native totals', async () => {
    mocks.get.mockResolvedValue(detail({ intervals_available: false, intervals: [], notice: 'The interval list does not agree with Nagios native durations.' }))
    renderDrawer()
    expect(await screen.findByText(/does not agree with Nagios native/)).toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'State timeline segments' })).not.toBeInTheDocument()
  })

  it('shows an error with Retry and recovers', async () => {
    mocks.get.mockRejectedValueOnce(new Error('Unable to read events from Nagios.')).mockResolvedValueOnce(detail())
    renderDrawer()
    expect(await screen.findByText('Unable to read events from Nagios.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('State durations')).toBeInTheDocument()
  })

  it('offers History only with system.history, closes on Escape and returns focus', async () => {
    mocks.get.mockResolvedValue(detail())
    const opener = document.createElement('button')
    document.body.appendChild(opener)
    opener.focus()
    const onClose = vi.fn()
    const view = renderDrawer(onClose)
    expect(await screen.findByRole('link', { name: 'Open History' })).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
    view.unmount()
    expect(document.activeElement).toBe(opener)
    mocks.permissions = []
    renderDrawer()
    await screen.findByText('State durations')
    expect(screen.queryByRole('link', { name: 'Open History' })).not.toBeInTheDocument()
  })
})

const summary = (over: Partial<AlertSummary> = {}): AlertSummary => ({
  period, source: 'Nagios archive', generated_at: '2024-01-02T00:00:00+00:00',
  filters: { scope: 'both', state_type: 'hard', include_recoveries: false, include_initial: false, hostname: null, service: null, states: [], policy: 'HARD problem events only; recoveries and initial-state entries excluded' },
  by: 'service', complete: true, notice: null,
  totals: { problem_events: 5, recovery_events: 2, host_problem_events: 1, service_problem_events: 4, distinct_hosts: 2, distinct_objects: 3, states: { CRITICAL: 4, DOWN: 1 } },
  ranking: [
    { rank: 1, hostname: 'a', service: 'http', total: 3, states: { CRITICAL: 3 }, first: T0, last: T0 + 5 },
    { rank: 2, hostname: 'b', service: null, total: 2, states: { DOWN: 1, CRITICAL: 1 }, first: T0, last: T0 + 9 },
  ],
  top: [], ...over,
})

describe('alert summary', () => {
  it('names the policy, separates recoveries and opens alerts for a row', async () => {
    mocks.get.mockResolvedValue(summary())
    const onOpenAlerts = vi.fn()
    render(<AlertSummaryReport query="period=last_24h&by=service" runKey={0} onStatus={vi.fn()} onOpenAlerts={onOpenAlerts} description="About" />)
    expect(await screen.findByText(/HARD problem events only/)).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: 'Open alerts' })[0])
    expect(onOpenAlerts).toHaveBeenCalledWith({ hostname: 'a', service: 'http' })
  })

  it('reports its totals as summary cards, with recoveries separate', async () => {
    mocks.get.mockResolvedValue(summary())
    const onCards = vi.fn()
    render(<AlertSummaryReport query="period=last_24h" runKey={0} onStatus={vi.fn()} onOpenAlerts={vi.fn()} description="About" onCards={onCards} />)
    await screen.findByText(/HARD problem events only/)
    const cards = onCards.mock.calls.map((c) => c[0]).find((c) => c.length > 0)
    expect(cards.map((c: { title: string; value: string }) => [c.title, c.value])).toEqual([
      ['Total Events', '7'], ['Recoveries', '2'], ['Problems', '5'], ['Hosts Affected', '2'],
    ])
  })

  it('shows no totals and blocks export for an incomplete result', async () => {
    mocks.get.mockResolvedValue(summary({ complete: false, totals: null, ranking: [], notice: 'Too many alert events to total for this period.' }))
    const onCards = vi.fn()
    render(<AlertSummaryReport query="period=last_24h" runKey={0} onStatus={vi.fn()} onOpenAlerts={vi.fn()} description="About" onCards={onCards} />)
    expect(await screen.findByText('Too many alert events to total for this period.')).toBeInTheDocument()
    expect(onCards).not.toHaveBeenCalledWith(expect.arrayContaining([expect.anything()]))
    expect(screen.queryByRole('button', { name: 'Export' })).not.toBeInTheDocument()
  })

  it('exports the full ranking with period, zone, policy and unit metadata', async () => {
    mocks.get.mockResolvedValue(summary())
    render(<AlertSummaryReport query="period=last_24h" runKey={0} onStatus={vi.fn()} onOpenAlerts={vi.fn()} description="About" />)
    await screen.findByText(/HARD problem events only/)
    fireEvent.click(screen.getByRole('button', { name: 'Export' }))
    fireEvent.click(screen.getByRole('button', { name: 'CSV' }))
    const [rows, format, name, meta] = mocks.export.mock.calls[0]
    expect(rows).toHaveLength(2)
    expect([format, name]).toEqual(['CSV', 'alert-summary-report'])
    expect(meta['Reporting time zone']).toContain('UTC')
    expect(meta['Event policy']).toMatch(/HARD problem events/)
    expect(meta.Units).toMatch(/alert events/)
  })
})

const histogram = (): AlertHistogram => ({
  period, source: 'Nagios archive', generated_at: '2024-01-02T00:00:00+00:00',
  filters: summary().filters, complete: true, recurring: true, notice: null, breakdown: 'weekday',
  bucketing_note: 'Buckets recur by wall-clock time in the reporting time zone.',
  series: { CRITICAL: [0, 2, 0, 0, 0, 0, 1] }, total: 3,
  buckets: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map((label, i) => ({
    label, total: [0, 2, 0, 0, 0, 0, 1][i], states: { CRITICAL: [0, 2, 0, 0, 0, 0, 1][i] } })),
})

describe('alert histogram', () => {
  it('labels recurring buckets, agrees chart and table and drills down by recurrence', async () => {
    mocks.get.mockResolvedValue(histogram())
    const onOpenAlerts = vi.fn()
    render(<AlertHistogramReport query="breakdown=weekday" runKey={0} onStatus={vi.fn()} onOpenAlerts={onOpenAlerts} description="About" />)
    expect(await screen.findByText(/recurring buckets, not a chronological chart/)).toBeInTheDocument()
    const table = screen.getByRole('table', { name: 'Histogram bucket counts' })
    expect(within(table).getAllByRole('row')).toHaveLength(8)   // header + seven weekdays, zero buckets kept
    const bar = screen.getByRole('button', { name: 'Monday: 2 alert events. Open matching alerts' })
    fireEvent.keyDown(bar, { key: 'Enter' })
    expect(onOpenAlerts).toHaveBeenCalledWith({ recurrence: 'weekday:1' })
    expect(screen.getByRole('group', { name: /Alert histogram by weekday: 3 events/ })).toBeInTheDocument()
  })
})

describe('insufficient history', () => {
  const none = [{ hostname: 'web-01', state: 'Unknown', uptimePct: null, upSeconds: 0, downSeconds: 0, unreachableSeconds: 0, knownSeconds: 0, lastCheck: null, lastStateChange: null }]

  it('host availability says there is nothing to measure when no host has known time', () => {
    render(<HostAvailabilityReportTable hosts={none} isLoading={false} />)
    expect(screen.getByRole('status')).toHaveTextContent('no recorded history for these hosts')
  })

  it('is not shown when any host has recorded time, while loading or for an empty list', () => {
    const { rerender } = render(<HostAvailabilityReportTable hosts={[{ ...none[0], knownSeconds: 5 }]} isLoading={false} />)
    expect(screen.queryByText(/no recorded history/)).not.toBeInTheDocument()
    rerender(<HostAvailabilityReportTable hosts={none} isLoading />)
    expect(screen.queryByText(/no recorded history/)).not.toBeInTheDocument()
    rerender(<HostAvailabilityReportTable hosts={[]} isLoading={false} />)
    expect(screen.queryByText(/no recorded history/)).not.toBeInTheDocument()
  })

  it('the detail drawer says so when the object has no known time', async () => {
    mocks.get.mockResolvedValue(detail({ totals: { ...detail().totals, known_seconds: 0, no_recorded_data_seconds: 1000,
      states: detail().totals.states.map((st) => ({ ...st, seconds: 0, pct_of_total: 0, pct_of_known: null })) } }))
    renderDrawer()
    expect(await screen.findByText(/no recorded state for this object/)).toBeInTheDocument()
  })
})

describe('host availability table', () => {
  const hosts = [{ hostname: 'web-01', state: 'Up', uptimePct: 80, upSeconds: 80, downSeconds: 20, unreachableSeconds: 0, knownSeconds: 100, lastCheck: null, lastStateChange: null }]

  it('has duration columns, no snapshot wording and a Details action', () => {
    const onDetails = vi.fn()
    render(<HostAvailabilityReportTable hosts={hosts} isLoading={false} onDetails={onDetails} />)
    expect(screen.queryByText(/snapshot/i)).not.toBeInTheDocument()
    expect(screen.getByText('Known time (s)')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Details for web-01' }))
    expect(onDetails).toHaveBeenCalledWith('web-01')
  })

  it('marks stale rows and withholds export', () => {
    render(<HostAvailabilityReportTable hosts={hosts} isLoading={false} stale />)
    expect(screen.getByRole('alert')).toHaveTextContent('cannot be exported')
    expect(screen.queryByRole('button', { name: /export/i })).not.toBeInTheDocument()
  })
})

describe('reports page scope and applied query', () => {
  const availabilityBody = { period, summary: { total: 0, up: 0, down: 0, unreachable: 0, uptime_pct: null }, hosts: [] }

  it('lists the views with summary cards first, then the others', () => {
    mocks.get.mockResolvedValue(availabilityBody)
    render(<MemoryRouter><ReportsPage /></MemoryRouter>)
    expect(within(screen.getByRole('tablist', { name: 'Report' })).getAllByRole('tab').map((t) => t.textContent)).toEqual([
      'Host Availability', 'Network Services', 'Alerts', 'Alert Summary', 'Notifications',
      'Hosts by OS', 'Device Services', 'Alert Histogram',
    ])
  })

  it('sends only parameters a report understands, after Run Report applies the draft', async () => {
    mocks.get.mockResolvedValue(availabilityBody)
    render(<MemoryRouter><ReportsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run Report' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: /Filters/ }))
    fireEvent.change(screen.getByLabelText('Host scope'), { target: { value: 'web-01' } })
    expect(screen.getByText(/Changes not applied/)).toBeInTheDocument()
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Run Report' })))
    expect(mocks.get).toHaveBeenLastCalledWith('/api/system/report/availability?period=last_24h&hostname=web-01')
    // Service scope is inapplicable to host availability.
    expect(screen.getByLabelText('Service scope')).toBeDisabled()
  })

  it('Clear filters resets the draft filters and applies on the next run', async () => {
    mocks.get.mockResolvedValue(availabilityBody)
    render(<MemoryRouter><ReportsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run Report' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: /Filters/ }))
    expect(screen.getByRole('button', { name: 'Clear filters' })).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Host scope'), { target: { value: 'web-01' } })
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Run Report' })))
    expect(mocks.get).toHaveBeenLastCalledWith('/api/system/report/availability?period=last_24h&hostname=web-01')
    expect(screen.getByRole('button', { name: 'Filters (1)' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    expect(screen.getByLabelText('Host scope')).toHaveValue('')
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Run Report' })))
    expect(mocks.get).toHaveBeenLastCalledWith('/api/system/report/availability?period=last_24h')
    expect(screen.getByRole('button', { name: 'Filters' })).toBeInTheDocument()
  })

  it('a failed rerun keeps the old rows but marks them stale with Retry and no export', async () => {
    mocks.get.mockResolvedValueOnce({ ...availabilityBody, summary: { ...availabilityBody.summary, total: 1 }, hosts: [{
      hostname: 'web-01', state: 'Up', uptime_pct: 100, up_seconds: 1, down_seconds: 0, unreachable_seconds: 0, known_seconds: 1,
      last_check: null, last_state_change: null }] })
    render(<MemoryRouter><ReportsPage /></MemoryRouter>)
    await screen.findByText('web-01')
    mocks.get.mockRejectedValueOnce(new Error('Nagios is down'))
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Run Report' })))
    expect(await screen.findByText(/cannot be exported/)).toBeInTheDocument()
    expect(screen.getByText('web-01')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /export/i })).not.toBeInTheDocument()
  })

  it('summary drilldown opens Alerts with the same period and the clicked object', async () => {
    mocks.get.mockImplementation((url: string) => Promise.resolve(url.includes('alert-summary') ? summary() : url.includes('/alerts') ? { period, alerts: [] } : availabilityBody))
    render(<MemoryRouter><ReportsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run Report' })).toBeEnabled())
    fireEvent.click(screen.getByRole('tab', { name: 'Alert Summary' }))
    fireEvent.change(screen.getByLabelText('Report period'), { target: { value: 'last_7d' } })
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Run Report' })))
    await screen.findByText(/HARD problem events only/)
    expect(mocks.get).toHaveBeenCalledWith('/api/system/report/alert-summary?period=last_7d&by=service')
    await act(async () => fireEvent.click(screen.getAllByRole('button', { name: 'Open alerts' })[0]))
    await waitFor(() => expect(mocks.get).toHaveBeenLastCalledWith('/api/system/report/alerts?period=last_7d&hostname=a&service=http'))
  })
})

describe('report formatting', () => {
  it('formats durations with units and export metadata names zone, source and generation time', () => {
    expect(formatDuration(0)).toBe('0 s')
    expect(formatDuration(3725)).toBe('1 h 2 min 5 s')
    expect(formatDuration(null)).toBe('—')
    const meta = exportMeta(period, { Units: 'seconds', Skipped: null }, '2024-01-02T00:00:00Z')
    expect(Object.keys(meta)).toEqual(['Report period', 'Reporting time zone', 'Generated at', 'Source', 'Units'])
  })
})
