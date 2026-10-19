import userEvent from '@testing-library/user-event'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Outlet } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import App from '../App'

vi.mock('../pages/SettingsPage', () => ({ SettingsPage: () => <div>Settings Page</div> }))

vi.mock('../pages/wagpakielaman', () => ({ TopologyPage: () => <div>Topology Page</div> }))

// Mock heavy/problematic child pages so App routing tests stay focused
vi.mock('../pages/DashboardPage', () => ({
  DashboardPage: () => <div>Dashboard Page</div>,
}))
vi.mock('../pages/DeviceInventoryPage', () => ({
  DeviceInventoryPage: () => <div>Device Inventory Page</div>,
}))
vi.mock('../pages/NetworkHealthPage', () => ({
  NetworkHealthPage: () => <div>Network Health Page</div>,
}))
vi.mock('../pages/SystemStatusPage', () => ({
  SystemStatusPage: () => <div>Network Status Page</div>,
}))
vi.mock('../pages/MaintenancePage', () => ({
  MaintenancePage: () => <div>Maintenance Page</div>,
}))
vi.mock('../pages/ManageAccountsPage', () => ({
  ManageAccountsPage: () => <div>Manage Accounts Page</div>,
}))
vi.mock('../pages/RemediationPage', () => ({
  RemediationPage: () => <div>Remediation Page</div>,
}))
vi.mock('../pages/PlaceholderPage', () => ({
  PlaceholderPage: ({ title }: { title: string }) => <div>{title} Page</div>,
}))
vi.mock('../components/layout/AdminLayout', () => ({
  AdminLayout: () => <Outlet />,
}))

function renderApp(initialEntry = '/') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App routing', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockResolvedValue(new Response('', { status: 401 }))
  })
  afterEach(() => vi.restoreAllMocks())

  it('does not expose login while checking the existing session', () => {
    vi.mocked(fetch).mockReturnValue(new Promise(() => {}))
    renderApp('/login')
    expect(screen.queryByRole('button', { name: /^log in$/i })).not.toBeInTheDocument()
  })

  it('redirects authenticated login navigation to an authorized page', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({
      data: { permissions: ['system.network_health'] },
    })))
    renderApp('/login')
    expect(await screen.findByText('Network Health Page')).toBeInTheDocument()
    expect(screen.queryByText('Log In to your Account')).not.toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith('/api/user/me', expect.objectContaining({ credentials: 'include' }))
  })

  it('keeps the login form hidden on a session-check failure and allows retry', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response('', { status: 503 }))
    renderApp('/login')
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to check your session')
    expect(screen.queryByText('Log In to your Account')).not.toBeInTheDocument()
    await userEvent.setup().click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByText('Log In to your Account')).toBeInTheDocument()
  })

  it('renders without crashing', async () => {
    renderApp('/')
    expect(await screen.findByText('Log In to your Account')).toBeInTheDocument()
  })

  it('redirects / to /login', async () => {
    renderApp('/')
    expect(await screen.findByText('Log In to your Account')).toBeInTheDocument()
  })

  it('sends a signed-in account without page grants to settings', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ data: { permissions: [] } })))
    renderApp('/login')
    expect(await screen.findByText('Settings Page')).toBeInTheDocument()
    expect(screen.queryByText('Log In to your Account')).not.toBeInTheDocument()
  })

  it('renders login page at /login route', async () => {
    renderApp('/login')
    // LoginPage renders "Log In to your Account" heading
    await waitFor(() => expect(screen.getByText('Log In to your Account')).toBeInTheDocument())
  })

  it('registers the Network Status page at /system-status', () => {
    renderApp('/system-status')
    expect(screen.getByText('Network Status Page')).toBeInTheDocument()
  })

  it('registers the Maintenance page at /maintenance', () => {
    renderApp('/maintenance')
    expect(screen.getByText('Maintenance Page')).toBeInTheDocument()
  })

  it('registers the Remediation page at /remediation', () => {
    renderApp('/remediation')
    expect(screen.getByText('Remediation Page')).toBeInTheDocument()
  })

  it('registers topology separately from Network Status', () => {
    renderApp('/topology')
    expect(screen.getByText('Topology Page')).toBeInTheDocument()
    expect(screen.queryByText('Network Status Page')).not.toBeInTheDocument()
  })

  it('renders wildcard * redirect to /login', async () => {
    renderApp('/this-does-not-exist')
    // After wildcard redirect to /login, LoginPage should be shown
    await waitFor(() => expect(screen.getByText('Log In to your Account')).toBeInTheDocument())
  })
})
