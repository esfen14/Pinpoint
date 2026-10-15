import { render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NetworkHealthPage } from '../pages/NetworkHealthPage'
import type { Bandwidth } from '../types/bandwidth'

// The side "Bandwidth" widget follows the interface chosen in the Interface Bandwidth card when
// NCPA bandwidth is not configured, and keeps showing the NCPA figure when it is.
vi.mock('../components/network-health/MiniSparkline', () => ({
  MiniSparkline: ({ data }: { data: number[] }) => <div data-testid="mini-sparkline" data-values={JSON.stringify(data)} />,
}))
vi.mock('../components/network-health/CpuUtilizationChart', () => ({ CpuUtilizationChart: () => null }))
vi.mock('../components/network-health/BandwidthChart', () => ({ BandwidthChart: () => <div data-testid="line-chart" /> }))
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: null, isLoading: false, hasPermission: () => true }),
}))
vi.mock('../contexts/SystemSettingsContext', () => ({
  useSystemSettings: () => ({ savedSettings: { dateTimeFormat: 'DD/MM/YYYY', timeZone: 'UTC+08:00' } }),
}))

const api = vi.hoisted(() => ({ getBandwidthChoices: vi.fn(), getBandwidth: vi.fn() }))
vi.mock('../lib/bandwidthApi', () => api)

const trends = vi.hoisted(() => ({ value: {} as Record<string, unknown> }))
const COUNTS = { total: 1, up: 1, down: 0, unreachable: 0, flapping: 0, in_downtime: 0 }
const SUMMARY = {
  hosts: COUNTS,
  services: { ...COUNTS, ok: 0, warning: 0, critical: 0, unknown: 0 },
  active_alerts: { total: 0, critical: 0, warning: 0, unknown: 0 },
  last_scan: { completed_at: null, is_running: false },
}
vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return {
    ...actual,
    apiGet: (path: string) => {
      if (path.startsWith('/api/system/network-health/summary')) return Promise.resolve(SUMMARY)
      if (path.startsWith('/api/system/network-health/trends')) return Promise.resolve(trends.value)
      return Promise.resolve(null)
    },
    apiPost: () => Promise.resolve(null),
  }
})

const points = (values: (number | null)[]) => values.map((bps, i) => ({ bucketStart: `2026-10-14T0${i}:00:00+00:00`, bps }))

const READING: Bandwidth = {
  hostname: 'switch-a',
  interface: { ifIndex: 2, name: 'eth0', speedBps: null },
  hours: 24,
  status: 'ok',
  inPoints: points([1_000_000, 2_000_000, 4_000_000]),
  outPoints: points([500_000, 500_000, 1_000_000]),
  latest: { timestamp: 'x', inBps: 4_000_000, outBps: 1_000_000, inUtilisationPct: null, outUtilisationPct: null },
}

const NO_NCPA = { ping: { configured: false, rta: [], packet_loss: [] }, ncpa: null, bandwidth: { configured: false, in: [], out: [] } }

function widget() {
  return screen.getByText('Bandwidth', { selector: 'span' }).closest('[class*="rounded-2xl"]') as HTMLElement
}

function renderPage() {
  return render(<MemoryRouter><NetworkHealthPage /></MemoryRouter>)
}

beforeEach(() => {
  trends.value = NO_NCPA
  api.getBandwidthChoices.mockReset().mockResolvedValue([{ hostname: 'switch-a', interfaces: [{ ifIndex: 2, name: 'eth0', speedBps: null }] }])
  api.getBandwidth.mockReset().mockResolvedValue(READING)
})

describe('Bandwidth widget on Network Health', () => {
  it('shows the selected interface: in + out of the latest reading, scaled', async () => {
    renderPage()

    await waitFor(() => expect(within(widget()).getByText('5.00')).toBeInTheDocument())
    expect(within(widget()).getByText('Mbit/s')).toBeInTheDocument()
    // 1.5, 2.5 and 5 Mbit/s summed per slice, in the widget's unit.
    expect(within(widget()).getByTestId('mini-sparkline')).toHaveAttribute('data-values', '[1.5,2.5,5]')
    expect(within(widget()).getByText('+233.3%')).toBeInTheDocument()
  })

  it('says Not configured while there is no reading', async () => {
    api.getBandwidthChoices.mockResolvedValue([])
    renderPage()

    await waitFor(() => expect(api.getBandwidthChoices).toHaveBeenCalled())
    expect(within(widget()).getByText('Not configured')).toBeInTheDocument()
    expect(within(widget()).getByText('—')).toBeInTheDocument()
  })

  it('says Not configured when the interface has insufficient data', async () => {
    api.getBandwidth.mockResolvedValue({ ...READING, status: 'insufficient_data', latest: null, inPoints: points([null]), outPoints: points([null]) })
    renderPage()

    await screen.findByText(/Insufficient data/)
    expect(within(widget()).getByText('Not configured')).toBeInTheDocument()
  })

  it('keeps the NCPA figure when NCPA bandwidth is configured', async () => {
    const point = (value: number) => ({ bucket_start: '2026-10-14T00:00:00+00:00', avg_value: value, unit: 'Mbps' })
    trends.value = { ...NO_NCPA, bandwidth: { configured: true, in: [point(2)], out: [point(1)] } }
    renderPage()

    await waitFor(() => expect(within(widget()).getByText('3.00')).toBeInTheDocument())
    expect(within(widget()).getByText('Mbps')).toBeInTheDocument()
    expect(within(widget()).queryByText('Mbit/s')).not.toBeInTheDocument()
  })
})
