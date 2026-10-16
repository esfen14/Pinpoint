import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ForecastList } from '../components/dashboard/ForecastList'
import { forecastBasis, fromForecastResponse, type ForecastApiResponse, type ForecastData } from '../types/forecast'

const NOW = new Date('2026-10-17T12:00:00Z')

function record(overrides: Record<string, unknown> = {}) {
  return {
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
    ...overrides,
  }
}

const WAITING = {
  hostname: 'new-01',
  service_name: 'ncpa-disk-5693',
  metric: 'disk/logical/|/used_percent',
  sample_count: 5,
  window_hours: 72,
}

function data(forecasts: unknown[] = [], insufficient: unknown[] = []): ForecastData {
  return fromForecastResponse({ forecasts, insufficient } as ForecastApiResponse)
}

describe('forecast types', () => {
  it('reads the wire record', () => {
    const [f] = data([record()]).forecasts
    expect(f).toMatchObject({
      hostname: 'web-01',
      serviceName: 'ncpa-disk-5693',
      kind: 'warning',
      threshold: 80,
      sampleCount: 70,
      windowHours: 72,
    })
  })

  it('tolerates a response with no forecast fields', () => {
    expect(fromForecastResponse({ items: [] } as unknown as ForecastApiResponse)).toEqual({ forecasts: [], insufficient: [] })
  })

  it('describes the basis in plain language', () => {
    expect(forecastBasis(72)).toBe('based on the last 3 days')
    expect(forecastBasis(24)).toBe('based on the last 24 hours')
    expect(forecastBasis(36)).toBe('based on the last 36 hours')
  })
})

describe('ForecastList', () => {
  it('lists what is running out, with the estimated date and basis', () => {
    const critical = record({
      hostname: 'db-01',
      service_name: 'ncpa-memory-5693',
      metric: 'memory/virtual/percent',
      kind: 'critical',
      threshold: 95,
      crossing_at: '2026-10-18T18:00:00+00:00',
    })
    render(<ForecastList data={data([record(), critical])} isLoading={false} error={null} now={NOW} />)

    expect(screen.getByRole('heading', { name: 'Running out soon' })).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    // Soonest first, as the server sends it; the list does not reorder.
    expect(items[0]).toHaveTextContent('web-01')
    expect(items[0]).toHaveTextContent('Disk space used')
    expect(items[0]).toHaveTextContent('warning level (80%)')
    expect(items[0]).toHaveTextContent('in about 6 days')
    expect(items[0]).toHaveTextContent('based on the last 3 days')
    expect(items[1]).toHaveTextContent('Memory used')
    expect(items[1]).toHaveTextContent('critical level (95%)')
    expect(items[1]).toHaveTextContent('in about 1 day')
  })

  it('labels the numbers as estimates, never failures', () => {
    render(<ForecastList data={data([record()])} isLoading={false} error={null} now={NOW} />)
    expect(screen.getByText(/estimate from a straight-line trend/i)).toBeInTheDocument()
  })

  it('shows a loading state', () => {
    render(<ForecastList data={null} isLoading error={null} now={NOW} />)
    expect(screen.getByText('Loading forecasts…')).toBeInTheDocument()
  })

  it('shows an error state', () => {
    render(<ForecastList data={null} isLoading={false} error="Unable to load forecasts." now={NOW} />)
    expect(screen.getByText('Unable to load forecasts.')).toBeInTheDocument()
  })

  it('shows an empty state when nothing is on course to run out', () => {
    render(<ForecastList data={data()} isLoading={false} error={null} now={NOW} />)
    expect(screen.getByText('Nothing is on course to reach a threshold.')).toBeInTheDocument()
  })

  it('says not enough data yet when only new services exist', () => {
    render(
      <ForecastList
        data={data([], [WAITING, { ...WAITING, hostname: 'new-02' }])}
        isLoading={false}
        error={null}
        now={NOW}
      />,
    )
    expect(screen.getByText(/Not enough data yet for 2 services/)).toBeInTheDocument()
    expect(screen.queryByText('Nothing is on course to reach a threshold.')).not.toBeInTheDocument()
  })

  it('still lists forecasts and mentions services that are waiting', () => {
    render(<ForecastList data={data([record()], [WAITING])} isLoading={false} error={null} now={NOW} />)
    expect(screen.getAllByRole('listitem')).toHaveLength(1)
    expect(screen.getByText(/1 service has not been watched long enough/)).toBeInTheDocument()
  })
})
