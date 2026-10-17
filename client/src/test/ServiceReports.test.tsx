import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NetworkServicesReportTable } from '../components/reports/NetworkServicesReportTable'
import { ExtraReports } from '../components/reports/ExtraReports'
import { ReportsPage } from '../pages/ReportsPage'
import { fromNetworkServicesResponse } from '../types/report'

const mocks = vi.hoisted(() => ({ get: vi.fn(), export: vi.fn() }))
vi.mock('../lib/api', () => ({ apiGet: mocks.get, apiPost: vi.fn().mockResolvedValue({}), errorMessage: (e: Error) => e.message }))
vi.mock('../utils/exportData', () => ({ exportRows: mocks.export }))
vi.mock('../contexts/SystemSettingsContext', () => ({ useSystemSettings: () => ({ settings: {
  exportFormats: ['CSV', 'XLS', 'PDF'], dateTimeFormat: 'YYYY-MM-DD HH:mm:ss', timeZone: 'UTC',
} }) }))

const seconds = { ok_seconds: 60, warning_seconds: 10, critical_seconds: 20, unknown_seconds: 10,
  scheduled_ok_seconds: 0, scheduled_warning_seconds: 0, scheduled_critical_seconds: 5, scheduled_unknown_seconds: 0,
  known_seconds: 100, no_data_seconds: 10, nagios_not_running_seconds: 20, unaccounted_seconds: 70,
  no_recorded_data_seconds: 100, window_seconds: 200, uptime_pct: 60 }
const current = { available: true, observed_at: '2026-10-17T12:00:00+00:00', notice: null }
const period = { period: 'custom', start: '2024-01-01T00:00:00+00:00', end: '2024-01-02T00:00:00+00:00' }
function network() {
  return { period, current_status: current,
    summary: { ...seconds, total_services: 12, total_instances: 12, ok: 0, warning: 0, critical: 12, unknown: 0, pending: 0, unavailable: 0 },
    services: Array.from({ length: 12 }, (_, n) => ({ ...seconds, service: `svc-${String(n).padStart(2,'0')}`,
      total_instances: 1, ok: 0, warning: 0, critical: 1, unknown: 0, pending: 0, unavailable: 0, instances: [] })) }
}
function device() {
  return { period, current_status: current, summary: seconds, total_hosts: 1, total_services: 12,
    hosts: [{ hostname: 'host-a', ...seconds, services: Array.from({ length: 12 }, (_, n) => ({
      ...seconds, service: `svc-${n}`, state: n === 0 ? null : n === 1 ? 'Pending' : 'Critical',
      last_check: null, last_state_change: null, plugin_output: null,
    })) }] }
}
const onStatus = vi.fn(), onCards = vi.fn()
beforeEach(() => { vi.clearAllMocks() })

async function exportAs(format: string) {
  fireEvent.click(screen.getByRole('button', { name: 'Export' }))
  fireEvent.click(screen.getByRole('button', { name: format }))
}

async function verifyRealExport(rows: Record<string, unknown>[], format: 'CSV' | 'XLS' | 'PDF') {
  const actual = await vi.importActual<typeof import('../utils/exportData')>('../utils/exportData')
  let contents = ''
  const blobs: Blob[] = []
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  const originalCreate = URL.createObjectURL, originalRevoke = URL.revokeObjectURL
  URL.createObjectURL = (blob: Blob) => { blobs.push(blob); return 'blob:service-report' }
  URL.revokeObjectURL = vi.fn()
  const write = vi.fn((html: string) => { contents = html })
  const print = vi.fn()
  const open = vi.spyOn(window, 'open').mockReturnValue({ document: { write, close: vi.fn() }, focus: vi.fn(), print } as unknown as Window)
  try {
    actual.exportRows(rows, format, 'service-duration-test')
    if (format === 'PDF') expect(print).toHaveBeenCalledOnce()
    else {
      expect(click).toHaveBeenCalledOnce()
      contents = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(String(reader.result))
        reader.onerror = reject
        reader.readAsText(blobs[0])
      })
    }
    expect(contents).toContain('Recorded time (seconds)')
    expect(contents).toContain('No recorded data (seconds)')
    expect(contents).toContain('Current')
    expect(contents).not.toMatch(/snapshot/i)
    expect(contents).toContain('100')
  } finally {
    URL.createObjectURL = originalCreate; URL.revokeObjectURL = originalRevoke
    click.mockRestore(); open.mockRestore()
  }
}

describe('service duration reports', () => {
  it.each(['CSV', 'XLS', 'PDF'])('network search/sort/pagination and full filtered %s export with seconds', async (format) => {
    const data = fromNetworkServicesResponse(network())
    render(<NetworkServicesReportTable services={data.services} isLoading={false} />)
    expect(screen.getByRole('columnheader', { name: 'Recorded time (seconds)' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'No recorded data (seconds)' })).toBeInTheDocument()
    expect(screen.queryByText(/snapshot/i)).not.toBeInTheDocument()
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(11)
    fireEvent.click(screen.getByRole('button', { name: 'Page 2', exact: true }))
    expect(screen.getByText('svc-11')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Page 1', exact: true }))
    await exportAs(format)
    await verifyRealExport(mocks.export.mock.calls[0][0], format as 'CSV' | 'XLS' | 'PDF')
    expect(mocks.export.mock.calls[0][0]).toHaveLength(12)
    const first = mocks.export.mock.calls[0][0][0]
    expect(first['Recorded time (seconds)']).toBe(100)
    expect(first['No recorded data (seconds)']).toBe(100)
    expect(first['Current Critical']).toBe(1)
    expect(JSON.stringify(first)).not.toMatch(/snapshot/i)
    fireEvent.click(screen.getByTitle('Sorted A → Z'))
    expect(within(screen.getByRole('table')).getAllByRole('row')[1]).toHaveTextContent('svc-11')
    fireEvent.change(screen.getByPlaceholderText('Search service'), { target: { value: 'svc-01' } })
    await exportAs(format)
    expect(mocks.export.mock.calls[1][0]).toHaveLength(1)
  })

  it.each(['CSV', 'XLS', 'PDF'])('device coverage, pending/missing current status, filter, pages and %s export', async (format) => {
    mocks.get.mockResolvedValue(device())
    render(<ExtraReports view="device-services" query="period=last_24h" runKey={0} onStatus={onStatus} onCards={onCards} />)
    await screen.findByText('Device Services Report')
    expect(screen.getByRole('columnheader', { name: 'Current state' })).toBeInTheDocument()
    expect(screen.getByText('Pending')).toBeInTheDocument()
    expect(screen.getByText('Unavailable')).toBeInTheDocument()
    expect(screen.queryByText(/snapshot/i)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Page 2', exact: true }))
    expect(screen.getByText('svc-11')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Page 1', exact: true }))
    fireEvent.click(screen.getByTitle('Sorted ascending'))
    expect(screen.getByTitle('Sorted descending')).toBeInTheDocument()
    expect(screen.getAllByText(/availability during recorded time/i).length).toBeGreaterThan(0)
    await exportAs(format)
    await verifyRealExport(mocks.export.mock.calls[0][0], format as 'CSV' | 'XLS' | 'PDF')
    expect(mocks.export.mock.calls[0][0]).toHaveLength(12)
    const first = mocks.export.mock.calls[0][0][0]
    expect(first['Unaccounted time (seconds)']).toBe(70)
    expect(first['Current last check']).toBe('')
    fireEvent.click(screen.getByRole('button', { name: 'Filter current state' }))
    fireEvent.click(screen.getByRole('button', { name: 'Pending' }))
    await exportAs(format)
    expect(mocks.export.mock.calls[1][0]).toHaveLength(1)
    fireEvent.change(screen.getByPlaceholderText('Search host or service'), { target: { value: 'not-found' } })
    expect(screen.getByText(/No services match/)).toBeInTheDocument()
  })

  it('clears device data and removes export on failed rerun; historical status failure has notice', async () => {
    mocks.get.mockResolvedValue({ ...device(), current_status: { available: false, observed_at: null, notice: 'Current status unavailable. Historical availability is still shown.' } })
    const view = render(<ExtraReports view="device-services" query="period=last_24h" runKey={0} onStatus={onStatus} onCards={onCards} />)
    await screen.findByText(/Current status unavailable/)
    mocks.get.mockRejectedValue(new Error('Retry report'))
    view.rerender(<ExtraReports view="device-services" query="period=last_7d" runKey={1} onStatus={onStatus} onCards={onCards} />)
    await waitFor(() => expect(onStatus).toHaveBeenCalledWith({ type: 'error', text: 'Retry report' }))
    expect(screen.queryByRole('button', { name: 'Export' })).not.toBeInTheDocument()
    expect(screen.queryByText('svc-0')).not.toBeInTheDocument()
  })

  it('network failed rerun clears prior rows and disables export; custom range reruns correct dates', async () => {
    mocks.get.mockImplementation((url: string) => Promise.resolve(url.includes('network-services') ? network() : { period, summary: {total: 0, up:0, down:0, unreachable:0, uptime_pct:null}, hosts:[] }))
    render(<ReportsPage />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run Report' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: 'Network Services' }))
    await screen.findByText('svc-00')
    mocks.get.mockRejectedValueOnce(new Error('Archive unavailable'))
    fireEvent.click(screen.getByRole('button', { name: 'Run Report' }))
    await screen.findByText('Archive unavailable')
    expect(screen.queryByText('svc-00')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Export' })).not.toBeInTheDocument()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'custom' } })
    fireEvent.change(screen.getByLabelText('Report start date'), { target: { value: '2024-01-01' } })
    fireEvent.change(screen.getByLabelText('Report end date'), { target: { value: '2024-01-02' } })
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Run Report' })))
    expect(mocks.get).toHaveBeenLastCalledWith('/api/system/report/network-services?period=custom&start=2024-01-01&end=2024-01-02')
  })
})
