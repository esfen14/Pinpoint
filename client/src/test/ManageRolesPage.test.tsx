import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ManageRolesPage } from '../pages/ManageRolesPage'

vi.mock('../hooks/useDisplayTime', () => ({
  useDisplayTime: () => ({ formatDate: (value: string) => value }),
}))

const apiGet = vi.fn()
const apiPut = vi.fn()

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return {
    ...actual,
    apiGet: (path: string) => apiGet(path),
    apiPut: (path: string, data?: unknown) => apiPut(path, data),
  }
})

const REQUIRED_PERMISSIONS = [
  'account.view',
  'account.edit',
  'account.info',
  'role.view',
  'role.edit',
  'role.info',
  'role.list',
]

describe('ManageRolesPage bootstrap administrator protection', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPut.mockReset()
    apiGet.mockImplementation((path: string) => {
      if (path === '/api/user/roles?per_page=100') {
        return Promise.resolve({
          items: [{
            id: 1,
            name: 'Administrator',
            description: 'Bootstrap role',
            is_active: true,
            is_locked: true,
            created_at: '2026-10-13T00:00:00+00:00',
          }],
        })
      }
      if (path === '/api/user/permissions/options') {
        return Promise.resolve({
          items: [
            ...REQUIRED_PERMISSIONS.map((name, index) => ({ id: index + 1, name })),
            { id: 99, name: 'system.dashboard' },
          ],
        })
      }
      if (path === '/api/user/roles/1') {
        return Promise.resolve({
          id: 1,
          name: 'Administrator',
          description: 'Bootstrap role',
          is_active: true,
          permissions: [
            ...REQUIRED_PERMISSIONS.map((name, index) => ({ id: index + 1, name })),
            { id: 99, name: 'system.dashboard' },
          ],
        })
      }
      return Promise.reject(new Error(`Unexpected path: ${path}`))
    })
  })

  it('explains and locks the permissions needed for account and role management', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <ManageRolesPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.queryByText('Loading roles…')).not.toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Edit role' }))

    expect(
      await screen.findByText(
        'This role belongs to the bootstrap administrator. Permissions required to manage accounts and roles cannot be removed.',
      ),
    ).toBeInTheDocument()
    for (const name of REQUIRED_PERMISSIONS) {
      expect(screen.getByRole('checkbox', { name })).toBeDisabled()
    }
    expect(screen.getByRole('checkbox', { name: 'system.dashboard' })).toBeEnabled()
  })
})
