import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NagiosLogPanel } from '../components/system-logs/NagiosLogPanel'
import { ApiError } from '../lib/api'
const state = vi.hoisted(() => ({ allowed: true, get: vi.fn() }))
vi.mock('../contexts/CurrentUserContext', () => ({ useCurrentUser: () => ({ hasPermission: () => state.allowed }) }))
vi.mock('../lib/api', async () => ({ ...await vi.importActual('../lib/api'), apiGet: state.get }))
const result = { lines: ['[1] HOST ALERT: web01;DOWN;HARD;1;[output redacted]'], available: true,
  truncated: true, max_lines: 500, max_bytes: 65536 }
beforeEach(() => { state.allowed = true; state.get.mockReset() })
describe('Nagios log', () => {
  it('loads latest lines and refreshes the fixed endpoint', async () => {
    state.get.mockResolvedValue(result)
    render(<NagiosLogPanel />)
    expect(screen.getByText('Loading Nagios log…')).toBeInTheDocument()
    expect(await screen.findByText(result.lines[0])).toBeInTheDocument()
    expect(screen.getByText(/only the latest/i)).toBeInTheDocument()
    expect(screen.getByText(/hostnames.*addresses/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Refresh Nagios log' }))
    await waitFor(() => expect(state.get).toHaveBeenCalledTimes(2))
    expect(state.get).toHaveBeenLastCalledWith('/api/system/log/nagios?lines=200')
  })
  it('distinguishes empty and unavailable files', async () => {
    state.get.mockResolvedValueOnce({ ...result, lines: [] }).mockResolvedValueOnce({ ...result, available: false, lines: [] })
    render(<NagiosLogPanel />)
    expect(await screen.findByText('No Nagios log entries are available.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Refresh Nagios log' }))
    expect(await screen.findByText(/Nagios log is unavailable/)).toBeInTheDocument()
  })
  it.each([new Error('Unable to load log.'), new ApiError('Denied', 403)])('shows errors and supports retry: %s', async (error) => {
    state.get.mockRejectedValueOnce(error).mockResolvedValueOnce(result)
    render(<NagiosLogPanel />)
    expect(await screen.findByRole('alert')).toHaveTextContent(error instanceof ApiError ? 'permission' : error.message)
    await userEvent.click(screen.getByRole('button', { name: 'Refresh Nagios log' }))
    expect(await screen.findByText(result.lines[0])).toBeInTheDocument()
  })
  it('does not render or fetch without system.logs', () => {
    state.allowed = false
    const view = render(<NagiosLogPanel />)
    expect(view.container).toBeEmptyDOMElement()
    expect(state.get).not.toHaveBeenCalled()
  })
})
