import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { BandwidthCard } from '../components/network-health/BandwidthCard'
import type { Bandwidth, BandwidthDevice } from '../types/bandwidth'

const api = vi.hoisted(() => ({ getBandwidthChoices: vi.fn(), getBandwidth: vi.fn() }))
vi.mock('../lib/bandwidthApi', () => api)

// jsdom has no layout engine: the chart is replaced by one that shows what it was given.
vi.mock('recharts', () => {
  const Nothing = () => null
  return {
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    LineChart: ({ children, data }: { children: React.ReactNode; data: { in: number | null }[] }) => (
      <div data-testid="line-chart" data-values={JSON.stringify(data.map((row) => row.in))}>{children}</div>
    ),
    YAxis: ({ label }: { label?: { value: string } }) => <span data-testid="y-axis-label">{label?.value}</span>,
    Line: ({ name }: { name: string }) => <span data-testid="line">{name}</span>,
    XAxis: Nothing, CartesianGrid: Nothing, Tooltip: Nothing, Legend: Nothing,
  }
})

const DEVICES: BandwidthDevice[] = [
  { hostname: 'switch-a', interfaces: [
    { ifIndex: 2, name: 'eth0', speedBps: 1_000_000_000 },
    { ifIndex: 5, name: 'eth1', speedBps: null },
  ] },
  { hostname: 'router-b', interfaces: [{ ifIndex: 1, name: 'wan', speedBps: 100_000_000 }] },
]

const points = (values: (number | null)[]) =>
  values.map((bps, i) => ({ bucketStart: `2026-10-14T0${i}:00:00+00:00`, bps }))

function reading(overrides: Partial<Bandwidth> = {}): Bandwidth {
  return {
    hostname: 'switch-a',
    interface: { ifIndex: 2, name: 'eth0', speedBps: 1_000_000_000 },
    hours: 24,
    status: 'ok',
    inPoints: points([2_000_000, 4_000_000, null]),
    outPoints: points([500_000, 1_000_000, null]),
    latest: {
      timestamp: '2026-10-14T02:00:00+00:00',
      inBps: 4_000_000, outBps: 1_000_000, inUtilisationPct: 0.4, outUtilisationPct: 0.1,
    },
    ...overrides,
  }
}

function renderCard() {
  return render(<MemoryRouter><BandwidthCard /></MemoryRouter>)
}

beforeEach(() => {
  api.getBandwidthChoices.mockReset().mockResolvedValue(DEVICES)
  api.getBandwidth.mockReset().mockResolvedValue(reading())
})

describe('states of the card', () => {
  it('shows a loading message first', () => {
    api.getBandwidthChoices.mockReturnValue(new Promise(() => {}))
    renderCard()
    expect(screen.getByText('Loading SNMP devices…')).toBeInTheDocument()
  })

  it('says so when no SNMP device exists', async () => {
    api.getBandwidthChoices.mockResolvedValue([])
    renderCard()

    expect(await screen.findByText(/No SNMP device is monitored yet/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Device')).not.toBeInTheDocument()
    expect(api.getBandwidth).not.toHaveBeenCalled()
  })

  it('points to Device Inventory when no interface is monitored', async () => {
    api.getBandwidthChoices.mockResolvedValue([{ hostname: 'switch-a', interfaces: [] }])
    renderCard()

    expect(await screen.findByText(/No interface is monitored yet/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Device Inventory' })).toHaveAttribute('href', '/device-inventory')
    expect(api.getBandwidth).not.toHaveBeenCalled()
  })

  it('shows the server error for the device list, and Retry loads it again', async () => {
    api.getBandwidthChoices.mockRejectedValueOnce(new ApiError('Boom.', 500))
    renderCard()

    expect(await screen.findByText('Boom.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByLabelText('Device')).toBeInTheDocument()
  })

  it('shows a server error for the rates instead of a chart', async () => {
    api.getBandwidth.mockRejectedValue(new ApiError('That interface is not monitored on this host.', 404))
    renderCard()

    expect(await screen.findByRole('alert')).toHaveTextContent('That interface is not monitored on this host.')
    expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument()
  })

  it('shows Insufficient data, not a broken chart', async () => {
    api.getBandwidth.mockResolvedValue(reading({ status: 'insufficient_data', latest: null, inPoints: points([null]), outPoints: points([null]) }))
    renderCard()

    expect(await screen.findByText(/Insufficient data/)).toBeInTheDocument()
    expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument()
  })

  it('shows a message when every point is empty', async () => {
    api.getBandwidth.mockResolvedValue(reading({ inPoints: points([null, null]), outPoints: points([null, null]) }))
    renderCard()

    expect(await screen.findByText('No bandwidth data in the selected time window.')).toBeInTheDocument()
    expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument()
  })

  it('tolerates an empty answer for the device list', async () => {
    api.getBandwidthChoices.mockResolvedValue([])
    expect(() => renderCard()).not.toThrow()
    await screen.findByText(/No SNMP device/)
  })
})

describe('choosing what to show', () => {
  it('starts with the first device that has an interface, for the last 24 hours', async () => {
    renderCard()

    await screen.findByTestId('line-chart')
    expect(api.getBandwidth).toHaveBeenCalledWith('switch-a', 2, 24)
    expect(screen.getByLabelText('Device')).toHaveValue('switch-a')
    expect(screen.getByLabelText('Interface')).toHaveValue('2')
  })

  it('lists the interfaces of the chosen device and loads the one picked', async () => {
    renderCard()
    await screen.findByTestId('line-chart')

    fireEvent.change(screen.getByLabelText('Interface'), { target: { value: '5' } })

    await waitFor(() => expect(api.getBandwidth).toHaveBeenLastCalledWith('switch-a', 5, 24))
    expect(screen.getByRole('option', { name: 'eth1' })).toBeInTheDocument()
  })

  it('switching device switches to its first interface', async () => {
    renderCard()
    await screen.findByTestId('line-chart')

    fireEvent.change(screen.getByLabelText('Device'), { target: { value: 'router-b' } })

    await waitFor(() => expect(api.getBandwidth).toHaveBeenLastCalledWith('router-b', 1, 24))
    expect(screen.getByLabelText('Interface')).toHaveValue('1')
  })

  it('offers only the ranges the server accepts and reloads on a change', async () => {
    renderCard()
    await screen.findByTestId('line-chart')

    fireEvent.click(screen.getByRole('button', { name: 'Time range' }))
    expect(screen.queryByRole('button', { name: 'Last 5 minutes' })).not.toBeInTheDocument()
    for (const label of ['Last hour', 'Last 6 hours', 'Last 7 days']) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument()
    }
    fireEvent.click(screen.getByRole('button', { name: 'Last 7 days' }))

    await waitFor(() => expect(api.getBandwidth).toHaveBeenLastCalledWith('switch-a', 2, 168))
  })
})

describe('the chart', () => {
  it('draws in and out lines and labels the axis with the unit', async () => {
    renderCard()

    await screen.findByTestId('line-chart')
    expect(screen.getAllByTestId('line').map((line) => line.textContent)).toEqual(['In', 'Out'])
    // The largest value is 4 Mbit/s, so the whole chart is in Mbit/s.
    expect(screen.getByTestId('y-axis-label')).toHaveTextContent('Mbit/s')
    expect(JSON.parse(screen.getByTestId('line-chart').getAttribute('data-values')!)).toEqual([2, 4, null])
  })

  it('scales to Gbit/s for a fast link', async () => {
    api.getBandwidth.mockResolvedValue(reading({ inPoints: points([2_500_000_000, 1_000_000_000]), outPoints: points([1, 2]) }))
    renderCard()

    await screen.findByTestId('line-chart')
    expect(screen.getByTestId('y-axis-label')).toHaveTextContent('Gbit/s')
    expect(JSON.parse(screen.getByTestId('line-chart').getAttribute('data-values')!)).toEqual([2.5, 1])
  })

  it('scales to kbit/s for light traffic', async () => {
    api.getBandwidth.mockResolvedValue(reading({ inPoints: points([12_000, 3_000]), outPoints: points([500, 600]) }))
    renderCard()

    await screen.findByTestId('line-chart')
    expect(screen.getByTestId('y-axis-label')).toHaveTextContent('kbit/s')
  })

  it('shows the latest rates, the utilisation and the link speed', async () => {
    renderCard()

    expect(await screen.findByText('4.00 Mbit/s · 0.4% of link')).toBeInTheDocument()
    expect(screen.getByText('1.00 Mbit/s · 0.1% of link')).toBeInTheDocument()
    expect(screen.getByText('1.00 Gbit/s')).toBeInTheDocument()
  })

  it('leaves out utilisation when the link speed is unknown', async () => {
    api.getBandwidthChoices.mockResolvedValue([{ hostname: 'switch-a', interfaces: [{ ifIndex: 2, name: 'eth0', speedBps: null }] }])
    api.getBandwidth.mockResolvedValue(reading({
      interface: { ifIndex: 2, name: 'eth0', speedBps: null },
      latest: { timestamp: 'x', inBps: 4_000_000, outBps: null, inUtilisationPct: null, outUtilisationPct: null },
    }))
    renderCard()

    expect(await screen.findByText('4.00 Mbit/s')).toBeInTheDocument()
    expect(screen.queryByText(/of link/)).not.toBeInTheDocument()
    expect(screen.queryByText('Link speed')).not.toBeInTheDocument()
  })

  it('explains the card in plain language', async () => {
    renderCard()
    await screen.findByTestId('line-chart')
    expect(screen.getByText(/Shows how much data an interface sends and receives/)).toBeInTheDocument()
  })
})
