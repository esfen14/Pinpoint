import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { StorageUsageCard } from '../components/dashboard/StorageUsageCard'
const access = vi.hoisted(() => ({ allowed: true }))
vi.mock('../contexts/CurrentUserContext', () => ({ useCurrentUser: () => ({ hasPermission: () => access.allowed }) }))
const filesystem = { free_bytes: 5 * 1024 ** 3, total_bytes: 10 * 1024 ** 3 }
const usage = { databases: [{ name: 'system.db', bytes: 2048, filesystem }],
  backups: { bytes: 4096, complete: true, filesystem }, archives: { bytes: null, complete: false, filesystem: null } }
describe('Storage usage', () => {
  it('shows sizes, free space and unavailable values', () => {
    render(<StorageUsageCard usage={usage} isLoading={false} error={null} />)
    expect(screen.getByText('system.db')).toBeInTheDocument()
    expect(screen.getByText('2 KiB')).toBeInTheDocument()
    expect(screen.getByText('4 KiB')).toBeInTheDocument()
    expect(screen.getAllByText(/5 GiB free/).length).toBe(2)
    expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0)
  })
  it('warns below the stated threshold and marks partial totals', () => {
    render(<StorageUsageCard usage={{ ...usage, backups: { bytes: 1024, complete: false,
      filesystem: { free_bytes: 9, total_bytes: 100 } } }} isLoading={false} error={null} />)
    expect(screen.getByRole('alert')).toHaveTextContent(/below 10%/i)
    expect(screen.getByText(/at least 1 KiB/i)).toBeInTheDocument()
  })
  it('shows loading, error and empty states', () => {
    const view = render(<StorageUsageCard usage={null} isLoading error={null} />)
    expect(screen.getByText('Loading storage usage…')).toBeInTheDocument()
    view.rerender(<StorageUsageCard usage={null} isLoading={false} error="Access denied (403)." />)
    expect(screen.getByText('Access denied (403).')).toBeInTheDocument()
    view.rerender(<StorageUsageCard usage={null} isLoading={false} error={null} />)
    expect(screen.getByText('Storage usage is unavailable.')).toBeInTheDocument()
  })
  it('hides without dashboard permission', () => {
    access.allowed = false
    const view = render(<StorageUsageCard usage={usage} isLoading={false} error={null} />)
    expect(view.container).toBeEmptyDOMElement()
    access.allowed = true
  })
})
