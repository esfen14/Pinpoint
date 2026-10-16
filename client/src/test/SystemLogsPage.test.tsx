import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, it, expect, vi } from 'vitest'
import { SystemLogsPage } from '../pages/SystemLogsPage'
const state = vi.hoisted(() => ({ allowed: true, get: vi.fn() }))
vi.mock('../contexts/CurrentUserContext', () => ({ useCurrentUser: () => ({ hasPermission: () => state.allowed }) }))
vi.mock('../contexts/SystemSettingsContext', () => ({ useSystemSettings: () => ({ settings: { exportFormats: ['CSV'], timeZone: 'Browser', dateTimeFormat: 'YYYY-MM-DD' } }) }))
vi.mock('../lib/api', async () => ({ ...await vi.importActual('../lib/api'), apiGet: state.get }))
beforeEach(() => {
  state.allowed = true
  state.get.mockReset().mockImplementation((url: string) => Promise.resolve(url.includes('/log/nagios')
    ? { lines: ['[1] [message redacted]'], available: true }
    : { items: [], total: 0, pages: 1, has_next: false, has_prev: false }))
})
describe('System Logs tabs', () => {
  it('preserves audit categories and loads the bounded log on selection', async () => {
    render(<SystemLogsPage />)
    expect(await screen.findByText('No logs match your search or filter')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Export Log' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Nagios log' }))
    expect(await screen.findByText('[1] [message redacted]')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Search')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Activity Log' }))
    await waitFor(() => expect(screen.getByPlaceholderText('Search')).toBeInTheDocument())
  })
  it('hides the page and skips requests without system.logs', () => {
    state.allowed = false
    const view = render(<SystemLogsPage />)
    expect(view.container).toBeEmptyDOMElement()
    expect(state.get).not.toHaveBeenCalled()
  })
})
