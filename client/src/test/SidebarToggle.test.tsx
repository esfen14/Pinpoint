import userEvent from '@testing-library/user-event'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { ReactNode } from 'react'
import { AdminLayout } from '../components/layout/AdminLayout'

vi.mock('../contexts/CurrentUserContext', () => ({
  CurrentUserProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  useCurrentUser: () => ({
    user: { permissions: ['system.dashboard'], firstName: 'Test', lastName: 'User', email: 't@test.com', role: 'Staff' },
    isLoading: false,
    hasPermission: (permission: string) => permission === 'system.dashboard',
  }),
}))
vi.mock('../contexts/SystemSettingsContext', () => ({
  SystemSettingsProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  useSystemSettings: () => ({ savedSettings: { notifications: false } }),
}))
vi.mock('../hooks/useDisplayTime', () => ({ useDisplayTime: () => ({ formatDate: () => '' }) }))
vi.mock('../components/layout/SessionTimeoutWatcher', () => ({ SessionTimeoutWatcher: () => null }))
vi.mock('../components/layout/MaintenanceBanner', () => ({ MaintenanceBanner: () => null }))

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Routes>
        <Route path="/" element={<AdminLayout />}>
          <Route path="dashboard" element={<div>Page content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

// The content column is the outer <main>; it carries the room left for the sidebar.
function contentColumn() {
  return screen.getByRole('main')
}

describe('Toggle sidebar button', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.restoreAllMocks())

  it('starts with the sidebar shown and the content beside it', () => {
    renderLayout()

    expect(screen.getByRole('complementary')).toBeInTheDocument()
    expect(contentColumn()).toHaveClass('ml-55')
    expect(screen.getByRole('button', { name: 'Toggle sidebar' })).toHaveAttribute('aria-expanded', 'true')
  })

  it('hides the sidebar and gives its space to the content', async () => {
    renderLayout()

    await userEvent.click(screen.getByRole('button', { name: 'Toggle sidebar' }))

    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
    expect(contentColumn()).not.toHaveClass('ml-55')
    expect(screen.getByRole('button', { name: 'Toggle sidebar' })).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByText('Page content')).toBeInTheDocument()
  })

  it('shows the sidebar again on a second click', async () => {
    renderLayout()
    const button = screen.getByRole('button', { name: 'Toggle sidebar' })

    await userEvent.click(button)
    await userEvent.click(button)

    expect(screen.getByRole('complementary')).toBeInTheDocument()
    expect(contentColumn()).toHaveClass('ml-55')
  })
})
