import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { MaintenancePage } from '../pages/MaintenancePage'
import { formatServerDateTime } from '../utils/formatDateTime'
import type { MaintenanceWindow } from '../types/maintenance'

const list = vi.fn()
const create = vi.fn()
const update = vi.fn()
const cancel = vi.fn()
vi.mock('../lib/maintenanceApi', () => ({
  listMaintenanceWindows: () => list(),
  createMaintenanceWindow: (...args: unknown[]) => create(...args),
  updateMaintenanceWindow: (...args: unknown[]) => update(...args),
  cancelMaintenanceWindow: (...args: unknown[]) => cancel(...args),
}))

// The page shows and reads times in the Time Zone setting; fix it so the test is exact.
let zone = 'UTC+08:00'
vi.mock('../hooks/useDisplayTime', () => ({
  useDisplayTime: () => ({
    timeZone: zone,
    dateTimeFormat: 'YYYY-MM-DD',
    formatDateTime: (value: string) => formatServerDateTime(value, 'YYYY-MM-DD', zone),
  }),
}))

function window_(over: Partial<MaintenanceWindow> = {}): MaintenanceWindow {
  return {
    id: 7,
    scope: { type: 'device', deviceId: 3, deviceName: 'web-01' },
    startAt: '2099-10-21T02:00:00Z',
    endAt: '2099-10-21T04:00:00Z',
    recurrence: 'none',
    recurrenceUntil: null,
    timeZone: 'UTC',
    comment: 'kernel update',
    status: 'active',
    nextOccurrence: { startAt: '2099-10-21T02:00:00Z', endAt: '2099-10-21T04:00:00Z' },
    lastOccurrenceSent: null,
    createdBy: 'Admin User',
    createdAt: '2099-10-01T00:00:00Z',
    occurrences: [],
    ...over,
  }
}

const devices = [{ id: 3, name: 'web-01' }, { id: 4, name: 'db-01' }]

function renderPage() {
  return render(<MemoryRouter><MaintenancePage /></MemoryRouter>)
}

function choose(label: string, option: string) {
  fireEvent.click(screen.getByRole('button', { name: label }))
  fireEvent.click(screen.getByRole('option', { name: option }))
}

function fillForm(over: { start?: string; end?: string; comment?: string } = {}) {
  fireEvent.change(screen.getByLabelText('Starts'), { target: { value: over.start ?? '2099-10-21T10:00' } })
  fireEvent.change(screen.getByLabelText('Ends'), { target: { value: over.end ?? '2099-10-21T12:00' } })
  fireEvent.change(screen.getByLabelText('Reason'), { target: { value: over.comment ?? 'patching' } })
}

beforeEach(() => {
  zone = 'UTC+08:00'
  list.mockReset().mockResolvedValue({ windows: [], devices })
  create.mockReset().mockResolvedValue(window_())
  update.mockReset().mockResolvedValue({ ...window_(), nagios_synced: true, nagios_message: null })
  cancel.mockReset().mockResolvedValue({ ...window_({ status: 'cancelled', nextOccurrence: null }), nagios_synced: true, nagios_message: null })
})

describe('MaintenancePage', () => {
  it('shows loading, then the empty state', async () => {
    renderPage()
    expect(screen.getByText(/Loading maintenance windows/)).toBeInTheDocument()
    expect(await screen.findByText(/No maintenance windows yet/)).toBeInTheDocument()
  })

  it('shows a load error and retries', async () => {
    list.mockRejectedValueOnce(new ApiError('Server is down', 500))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Server is down')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByText(/No maintenance windows yet/)).toBeInTheDocument()
  })

  it('lists windows with scope, next occurrence in the display time zone, repeat and status', async () => {
    list.mockResolvedValue({ windows: [window_(), window_({ id: 8, scope: { type: 'all', deviceId: null, deviceName: null }, recurrence: 'weekly', comment: 'weekly patching' })], devices })
    renderPage()
    expect(await screen.findByText('kernel update')).toBeInTheDocument()
    expect(screen.getByText('web-01')).toBeInTheDocument()
    expect(screen.getByText('All monitored devices')).toBeInTheDocument()
    expect(screen.getByText('Every week')).toBeInTheDocument()
    // 02:00Z shown at UTC+08:00
    expect(screen.getAllByText('2099-10-21 10:00 AM').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Scheduled').length).toBe(2)
  })

  it('shows a failed occurrence with its reason', async () => {
    list.mockResolvedValue({ windows: [window_({ occurrences: [{ startAt: '2099-10-21T02:00:00Z', endAt: '2099-10-21T04:00:00Z', status: 'failed', attempts: 3, error: 'web-01: Nagios is not reading its command pipe.' }] })], devices })
    renderPage()
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Failed for 2099-10-21 10:00 AM')
    expect(alert).toHaveTextContent('Nagios is not reading its command pipe.')
  })

  it('labels the two maintenance concepts and links them', async () => {
    renderPage()
    await screen.findByText(/No maintenance windows yet/)
    expect(screen.getByText(/silences alerts/)).toBeInTheDocument()
    expect(screen.getByText(/does not silence any alert/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Settings → System/ })).toHaveAttribute('href', '/settings#system')
  })

  it('creates a window: times typed in the display zone are sent as UTC', async () => {
    renderPage()
    await screen.findByText(/No maintenance windows yet/)
    fireEvent.click(screen.getByRole('button', { name: /New window/ }))
    fillForm()
    choose('Devices', 'db-01')
    choose('Repeats', 'Every day')
    fireEvent.click(screen.getByRole('button', { name: 'Create window' }))

    await waitFor(() => expect(create).toHaveBeenCalledWith({
      deviceId: 4,
      startAt: '2099-10-21T02:00:00.000Z',
      endAt: '2099-10-21T04:00:00.000Z',
      recurrence: 'daily',
      recurrenceUntil: null,
      timeZone: 'UTC',
      comment: 'patching',
    }))
    expect(await screen.findByText('Maintenance window created.')).toBeInTheDocument()
    expect(list).toHaveBeenCalledTimes(2)
    expect(screen.queryByRole('form', { name: 'New maintenance window' })).not.toBeInTheDocument()
  })

  it('blocks an invalid window before calling the server', async () => {
    renderPage()
    await screen.findByText(/No maintenance windows yet/)
    fireEvent.click(screen.getByRole('button', { name: /New window/ }))
    fillForm({ end: '2099-10-21T09:00' })
    fireEvent.click(screen.getByRole('button', { name: 'Create window' }))
    expect(screen.getByRole('alert')).toHaveTextContent('The end must be after the start.')
    expect(create).not.toHaveBeenCalled()
  })

  it('shows the server error and keeps the form open', async () => {
    create.mockRejectedValue(new ApiError('Device is paused, so it has no Nagios downtime to schedule.', 400))
    renderPage()
    await screen.findByText(/No maintenance windows yet/)
    fireEvent.click(screen.getByRole('button', { name: /New window/ }))
    fillForm()
    fireEvent.click(screen.getByRole('button', { name: 'Create window' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Device is paused')
    expect(screen.getByRole('button', { name: 'Create window' })).toBeEnabled()
  })

  it('edits a window with its times shown in the display zone', async () => {
    list.mockResolvedValue({ windows: [window_()], devices })
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Edit window 7' }))
    expect(screen.getByLabelText('Starts')).toHaveValue('2099-10-21T10:00')
    expect(screen.getByLabelText('Ends')).toHaveValue('2099-10-21T12:00')
    expect(screen.getByRole('button', { name: 'Devices' })).toHaveTextContent('web-01')
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'moved' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() => expect(update).toHaveBeenCalledWith(7, expect.objectContaining({ comment: 'moved', startAt: '2099-10-21T02:00:00.000Z', deviceId: 3 })))
    expect(await screen.findByText('Maintenance window updated.')).toBeInTheDocument()
  })

  it('tells the user when Nagios could not be updated', async () => {
    list.mockResolvedValue({ windows: [window_()], devices })
    update.mockResolvedValue({ ...window_(), nagios_synced: false, nagios_message: 'Saved in PinPoint, but Nagios was not updated (pipe). Notifications may continue.' })
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Edit window 7' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByText(/Nagios was not updated/)).toBeInTheDocument()
    expect(screen.getByText('Maintenance window updated.')).toBeInTheDocument()
  })

  it('cancels only after a second click', async () => {
    list.mockResolvedValue({ windows: [window_()], devices })
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Cancel window 7' }))
    expect(cancel).not.toHaveBeenCalled()
    const row = screen.getByText('Cancel this window?').closest('tr') as HTMLElement
    fireEvent.click(within(row).getByRole('button', { name: 'Yes, cancel it' }))
    await waitFor(() => expect(cancel).toHaveBeenCalledWith(7))
    expect(await screen.findByText('Maintenance window cancelled.')).toBeInTheDocument()
  })

  it('keeps the window when the user backs out of cancelling', async () => {
    list.mockResolvedValue({ windows: [window_()], devices })
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Cancel window 7' }))
    fireEvent.click(screen.getByRole('button', { name: 'Keep it' }))
    expect(cancel).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Edit window 7' })).toBeInTheDocument()
  })

  it('offers no actions on a cancelled window', async () => {
    list.mockResolvedValue({ windows: [window_({ status: 'cancelled', nextOccurrence: null })], devices })
    renderPage()
    expect(await screen.findByText('Cancelled')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Edit window 7' })).not.toBeInTheDocument()
  })
})
