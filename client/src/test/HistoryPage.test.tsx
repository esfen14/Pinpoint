import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { HistoryPage } from '../pages/HistoryPage'
import { PageAccessGuard } from '../components/layout/PageAccessGuard'

let permissions: string[] = ['system.history']
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({ user: { permissions }, isLoading: false, hasPermission: (p: string) => permissions.includes(p) }),
}))
vi.mock('../contexts/SystemSettingsContext', () => ({
  useSystemSettings: () => ({ settings: { timeZone: 'Browser', dateTimeFormat: 'YYYY-MM-DD' } }),
}))
const apiGet = vi.fn()
vi.mock('../lib/api', async () => ({
  ...(await vi.importActual<typeof import('../lib/api')>('../lib/api')),
  apiGet: (path: string) => apiGet(path),
}))
const alert = {
  event_id: '1790000000:alert-id', timestamp: 1790000000, type: 'service', hostname: 'web', service_name: 'HTTP',
  previous_state: 'OK', new_state: 'CRITICAL', state_type: 'hard', duration_seconds: 60,
  plugin_output: 'Failure', acknowledged: true,
}
const nagios = {
  event_id: '1790000020:notification-id', timestamp: 1790000020, source: 'nagios', type: 'service', hostname: 'web', service_name: 'HTTP',
  state: 'CRITICAL', contact: 'admin', method: 'email', message: 'Failure',
}
const pinpoint = { ...nagios, event_id: undefined, id: 4, source: 'pinpoint', type: 'scan', hostname: 'Pinpoint',
  service_name: 'Network scan', contact: '', method: '', state: 'SUCCESS', message: 'Finished' }
const page = (items: unknown[], pages = 1) => ({ items, page: 1, per_page: 25, total: items.length, pages })
function renderPage() {
  return render(<MemoryRouter initialEntries={['/history']}><Routes>
    <Route path="/history" element={<PageAccessGuard><HistoryPage /></PageAccessGuard>} />
    <Route path="/settings" element={<div>Settings page</div>} />
  </Routes></MemoryRouter>)
}
function query(path: string) { return new URLSearchParams(path.split('?')[1]) }

beforeEach(() => {
  permissions = ['system.history']
  apiGet.mockReset()
  apiGet.mockImplementation((path: string) => {
    if (path.includes('/alerts/detail')) return Promise.resolve({ ...alert, plugin_output: 'Full failure',
      ack: { acknowledged_by: 'Alice', acknowledged_at: '2026-09-20T00:00:00Z', comment: 'Investigating' },
      recovery_duration: null, linked_notifications: [{ event_id: nagios.event_id, timestamp: nagios.timestamp, contact: 'admin', state: 'CRITICAL', message: 'Failure' }] })
    if (path.includes('/notifications/detail')) return Promise.resolve({ ...nagios, contacts: ['admin'],
      linked_alert: { event_id: alert.event_id, timestamp: alert.timestamp, new_state: 'CRITICAL', prev_state: 'OK' }, message: 'Full message' })
    if (path.includes('/notifications?')) return Promise.resolve(page(query(path).has('event_id') ? [nagios] : [nagios, pinpoint]))
    return Promise.resolve(page([alert]))
  })
})

describe('HistoryPage', () => {
  it('guards direct access without system.history', async () => {
    permissions = []
    renderPage()
    expect(await screen.findByText('Settings page')).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('loads alerts, applies combined filters, sorts and paginates', async () => {
    const user = userEvent.setup()
    renderPage()
    expect(await screen.findByText('web')).toBeInTheDocument()
    expect(query(apiGet.mock.calls[0][0]).get('preset')).toBe('24h')
    await user.selectOptions(screen.getByLabelText('Type'), 'service')
    await user.type(screen.getByLabelText('Host'), 'web')
    await user.selectOptions(screen.getByLabelText('Acknowledged'), 'acknowledged')
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    await waitFor(() => expect(query(apiGet.mock.lastCall![0]).get('ack_filter')).toBe('acknowledged'))
    expect(query(apiGet.mock.lastCall![0]).get('hostname')).toBe('web')
    expect(query(apiGet.mock.lastCall![0]).get('type')).toBe('service')
    await user.selectOptions(screen.getByLabelText('Rows per page'), '50')
    await waitFor(() => expect(query(apiGet.mock.lastCall![0]).get('per_page')).toBe('50'))
    await user.click(screen.getByRole('button', { name: /Host/ }))
    await waitFor(() => expect(query(apiGet.mock.lastCall![0]).get('sort_by')).toBe('hostname'))
  })

  it('expands alert detail with full output, acknowledgement and related notification navigation', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click((await screen.findByText('Failure')).closest('tr')!)
    expect(await screen.findByText('Full failure')).toBeInTheDocument()
    expect(screen.getByText(/Acknowledged by/)).toHaveTextContent('Alice')
    await user.click(screen.getByRole('button', { name: /View notification/ }))
    await waitFor(() => expect(apiGet.mock.calls.some(([path]) => path.includes('/notifications?') && query(path).get('event_id') === nagios.event_id)).toBe(true))
    expect(query(apiGet.mock.calls.find(([path]) => path.includes('/notifications?') && query(path).has('event_id'))![0]).get('preset')).toBeNull()
    expect(await screen.findByText('Full message')).toBeInTheDocument()
  })

  it('shows Nagios and Pinpoint events, source filter, and exact linked alert', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click(screen.getByRole('button', { name: 'Notifications History' }))
    expect(await screen.findAllByText('Pinpoint')).toHaveLength(3)
    expect(screen.getAllByText('Nagios').length).toBeGreaterThan(0)
    await user.selectOptions(screen.getByLabelText('Source'), 'pinpoint')
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    await waitFor(() => expect(query(apiGet.mock.lastCall![0]).get('source')).toBe('pinpoint'))
    await user.click(screen.getByText('admin').closest('tr')!)
    expect(await screen.findByText('Full message')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'View in Alerts History' }))
    await waitFor(() => expect(apiGet.mock.calls.some(([path]) => path.includes('/alerts?') && query(path).get('event_id') === alert.event_id)).toBe(true))
    expect(query(apiGet.mock.calls.find(([path]) => path.includes('/alerts?') && query(path).has('event_id'))![0]).get('preset')).toBeNull()
    expect(await screen.findByText('Full failure')).toBeInTheDocument()
  })

  it('shows empty and error states and allows retry', async () => {
    const user = userEvent.setup()
    apiGet.mockResolvedValueOnce(page([])).mockRejectedValueOnce(new Error('Offline')).mockResolvedValueOnce(page([alert]))
    renderPage()
    expect(await screen.findByText(/No alert history is available yet/)).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Time range'), '7d')
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    expect(await screen.findByText(/Offline/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Refresh' }))
    expect(await screen.findByText('web')).toBeInTheDocument()
  })
})


describe('HistoryPage: custom notifications', () => {
  const COMMENT = 'PinPoint automatic recovery did not succeed: action restart-web ended failed (run 7).'
  const customItem = { ...nagios, event_id: '1790000030:custom-id', timestamp: 1790000030, state: '', contact: 'nagiosadmin',
    method: 'notify-service-by-email', message: 'HTTP CRITICAL - Connection refused', is_custom: true, comment: COMMENT }

  it('labels the notification Custom and shows its comment in the list and the detail', async () => {
    apiGet.mockImplementation((path: string) => {
      if (path.includes('/notifications/detail')) return Promise.resolve({ ...customItem, contacts: ['nagiosadmin'], linked_alert: null })
      if (path.includes('/notifications?')) return Promise.resolve(page([customItem]))
      return Promise.resolve(page([alert]))
    })
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('web')
    await user.click(screen.getByRole('button', { name: 'Notifications History' }))
    const row = (await screen.findByText(/notify-service-by-email/)).closest('tr') as HTMLElement
    expect(row).toHaveTextContent('Custom')
    expect(row).toHaveTextContent(COMMENT)
    await user.click(row)
    expect(await screen.findByText('Custom notification')).toBeInTheDocument()
    expect(screen.getByText(COMMENT)).toBeInTheDocument()
    expect(await screen.findByText('HTTP CRITICAL - Connection refused')).toBeInTheDocument()
  })

  it('leaves an ordinary notification unlabelled', async () => {
    apiGet.mockImplementation((path: string) => {
      if (path.includes('/notifications?')) return Promise.resolve(page([nagios]))
      return Promise.resolve(page([alert]))
    })
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('web')
    await user.click(screen.getByRole('button', { name: 'Notifications History' }))
    const row = (await screen.findByText(/email · Failure/)).closest('tr') as HTMLElement
    expect(row).not.toHaveTextContent('Custom')
  })
})
