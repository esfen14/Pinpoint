import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import { DashboardPage } from '../pages/DashboardPage'
vi.mock('../contexts/CurrentUserContext', () => ({ useCurrentUser: () => ({ hasPermission: (name: string) => name === 'system.dashboard' }) }))
vi.mock('../contexts/SystemSettingsContext', () => ({ useSystemSettings: () => ({ settings: { dashboardRefreshRate: 0, dateTimeFormat: 'YYYY-MM-DD', timeZone: 'Browser' } }) }))
vi.mock('../lib/api', async () => ({
  ...await vi.importActual('../lib/api'),
  apiGet: async (path: string) => {
    if (path === '/api/system/dashboard/status') return { nagios: { running: true }, storage_usage: {
      databases: [{ name: 'system.db', bytes: 1024, filesystem: { free_bytes: 100, total_bytes: 1000 } }],
      backups: { bytes: null, complete: false, filesystem: null },
      archives: { bytes: null, complete: false, filesystem: null },
    } }
    throw new Error('Other dashboard sources unavailable')
  },
}))
describe('Independent appliance status', () => {
  it('shows storage even when unrelated sources fail or require another permission', async () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('1 KiB')).toBeInTheDocument()
    expect(screen.getByText('system.db')).toBeInTheDocument()
  })
})
