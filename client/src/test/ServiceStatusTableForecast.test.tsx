import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ServiceStatusTable } from '../components/system-status/ServiceStatusTable'
import { fromForecastResponse, type ForecastData } from '../types/forecast'
import type { ServiceRow } from '../types/service'

const NOW = new Date('2026-10-17T12:00:00Z')

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

const FORECASTS = fromForecastResponse({
  forecasts: [
    {
      hostname: 'web-01',
      service_name: 'ncpa-disk-5693',
      metric: 'disk/logical/|/used_percent',
      kind: 'warning',
      threshold: 80,
      crossing_at: '2026-10-23T12:00:00+00:00',
      slope_per_hour: 0.3,
      r_squared: 0.97,
      sample_count: 70,
      window_hours: 72,
      current_value: 61.5,
      unit: '%',
      computed_at: '2026-10-17T11:30:00+00:00',
    },
  ],
  insufficient: [
    {
      hostname: 'new-01',
      service_name: 'ncpa-disk-5693',
      metric: 'disk/logical/|/used_percent',
      sample_count: 5,
      window_hours: 72,
    },
  ],
})

function renderTable(forecasts?: ForecastData) {
  return render(
    <ServiceStatusTable
      services={[row('web-01', 'ncpa-disk-5693'), row('new-01', 'ncpa-disk-5693'), row('web-01', 'http-80-TCP')]}
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
      total={3}
      hasNext={false}
      hasPrev={false}
      onPageChange={vi.fn()}
      onAcknowledge={vi.fn()}
      onUnacknowledge={vi.fn()}
      forecasts={forecasts}
      forecastNow={NOW}
    />,
  )
}

describe('ServiceStatusTable forecast badge', () => {
  it('shows the estimate and its basis on a service on course to cross a threshold', () => {
    renderTable(FORECASTS)
    const badge = screen.getByText('Estimate: warning level in about 6 days')
    expect(badge).toHaveAttribute('title', expect.stringContaining('based on the last 3 days'))
    expect(badge).toHaveAttribute('title', expect.stringContaining('Disk space used'))
  })

  it('shows not enough data yet for a new service', () => {
    renderTable(FORECASTS)
    expect(screen.getByText('Not enough data yet')).toBeInTheDocument()
  })

  it('shows no badge on a service with nothing to forecast', () => {
    renderTable(FORECASTS)
    const plain = screen.getByText('http-80-TCP').closest('tr') as HTMLElement
    expect(plain).not.toHaveTextContent('Estimate')
    expect(plain).not.toHaveTextContent('Not enough data')
  })

  it('works without forecast data', () => {
    renderTable()
    expect(screen.queryByText(/Estimate:/)).not.toBeInTheDocument()
    expect(screen.queryByText('Not enough data yet')).not.toBeInTheDocument()
  })
})
