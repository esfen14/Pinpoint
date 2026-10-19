import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { NetworkPerformanceSection } from '../components/dashboard/NetworkPerformanceSection'
import { NetworkStatusOverview } from '../components/dashboard/NetworkStatusOverview'
import { RecentOutageTable } from '../components/dashboard/RecentOutageTable'
import { ResourceUtilizationSection } from '../components/dashboard/ResourceUtilizationSection'

// Charts render SVG through recharts, which jsdom cannot lay out; the headers are what is under test.
vi.mock('../components/dashboard/NetworkChart', () => ({
  NetworkChart: () => <div data-testid="network-chart" />,
}))
vi.mock('../contexts/SystemSettingsContext', () => ({
  useSystemSettings: () => ({
    settings: { dashboardRefreshRate: 0, dateTimeFormat: 'YYYY-MM-DD', timeZone: 'UTC+08:00' },
  }),
}))

// Overview cards must not show a "more options" button: it opened nothing, and a control that looks clickable but is not misleads users.
describe('Overview card headers', () => {
  it('shows no "More options" button on Network Status Overview', () => {
    render(<NetworkStatusOverview up={3} down={1} isLoading />)
    expect(screen.getByText('Network Status Overview')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'More options' })).not.toBeInTheDocument()
  })

  it('shows no "More options" button on Network Performance', () => {
    render(<NetworkPerformanceSection pingMetrics={null} rtaTrend={[]} isLoading />)
    expect(screen.getByText('Network Performance')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'More options' })).not.toBeInTheDocument()
  })

  it('shows no "More options" button on Average Resource Utilization and keeps the period picker', () => {
    render(<ResourceUtilizationSection cpuTrend={[]} isLoading hours={24} onHoursChange={() => {}} />)
    expect(screen.getByText('Average Resource Utilization')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Last 24 hours/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'More options' })).not.toBeInTheDocument()
  })

  it('shows no "More options" button on Active Alerts and keeps Acknowledge all', () => {
    const alert = {
      id: 1, host: 'switch-1', service: 'snmp-uptime-161', state: 'CRITICAL', message: 'timeout',
      time: '2026-10-19T00:00:00Z', ack: false,
    } as unknown as Parameters<typeof RecentOutageTable>[0]['alerts'][number]
    render(<RecentOutageTable alerts={[alert]} isLoading={false} onAcknowledge={() => {}} onAcknowledgeAll={() => {}} />)
    expect(screen.getByText('Active Alerts')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Acknowledge all/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'More options' })).not.toBeInTheDocument()
  })
})
