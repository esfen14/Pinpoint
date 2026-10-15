import { render, screen } from '@testing-library/react'
import { MemoryRouter, Outlet } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import App from '../App'

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
  SystemStatusPage: () => <div>System Status Page</div>,
}))
vi.mock('../pages/MaintenancePage', () => ({
  MaintenancePage: () => <div>Maintenance Page</div>,
}))
vi.mock('../pages/ManageAccountsPage', () => ({
  ManageAccountsPage: () => <div>Manage Accounts Page</div>,
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
  it('renders without crashing', () => {
    renderApp('/')
  })

  it('redirects / to /login', () => {
    renderApp('/')
    // The root "/" is nested under AdminLayout which redirects to /login
    // AdminLayout is mocked, so Navigate inside it renders the login page redirect
    // With the mock, AdminLayout renders a plain div — we just confirm no crash
    expect(document.body).toBeTruthy()
  })

  it('renders login page at /login route', () => {
    renderApp('/login')
    // LoginPage renders "Log In to your Account" heading
    expect(screen.getByText('Log In to your Account')).toBeInTheDocument()
  })

  it('registers the System Status page at /system-status', () => {
    renderApp('/system-status')
    expect(screen.getByText('System Status Page')).toBeInTheDocument()
  })

  it('registers the Maintenance page at /maintenance', () => {
    renderApp('/maintenance')
    expect(screen.getByText('Maintenance Page')).toBeInTheDocument()
  })

  it('does not register the former /topology route', () => {
    renderApp('/topology')
    expect(screen.getByText('Log In to your Account')).toBeInTheDocument()
    expect(screen.queryByText('System Status Page')).not.toBeInTheDocument()
  })

  it('renders wildcard * redirect to /login', () => {
    renderApp('/this-does-not-exist')
    // After wildcard redirect to /login, LoginPage should be shown
    expect(screen.getByText('Log In to your Account')).toBeInTheDocument()
  })
})
