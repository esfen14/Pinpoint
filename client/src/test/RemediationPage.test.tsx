import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { RemediationPage } from '../pages/RemediationPage'
import type { RemediationAction, RemediationRun } from '../types/remediation'

const api = vi.hoisted(() => ({
  getActionTypes: vi.fn(),
  listActions: vi.fn(),
  createAction: vi.fn(),
  updateAction: vi.fn(),
  deleteAction: vi.fn(),
  listRuns: vi.fn(),
  getRun: vi.fn(),
}))

vi.mock('../lib/remediationApi', async () => {
  const actual = await vi.importActual<typeof import('../lib/remediationApi')>('../lib/remediationApi')
  return { ...api, fieldErrors: actual.fieldErrors }
})

let permissions: string[] = []
vi.mock('../contexts/CurrentUserContext', () => ({
  useCurrentUser: () => ({
    user: { permissions },
    isLoading: false,
    hasPermission: (name: string) => permissions.includes(name),
  }),
}))
vi.mock('../contexts/SystemSettingsContext', () => ({
  useSystemSettings: () => ({ settings: { dateTimeFormat: 'DD/MM/YYYY', timeZone: 'UTC+00:00' } }),
}))

const TYPES = [{ key: 'record_only', label: 'Record only', description: 'Changes nothing.', parameters: [] }]

function action(overrides: Partial<RemediationAction> = {}): RemediationAction {
  return {
    id: 1, name: 'restart-web', actionType: 'record_only', scopeKind: 'service', hostPattern: 'web-*',
    servicePattern: 'HTTP', parameters: {}, enabled: true, maxRunsPerHour: 2, cooldownSeconds: 600,
    version: 3, updatedAt: '2026-10-14T10:00:00', updatedBy: 1, ...overrides,
  }
}

function run(overrides: Partial<RemediationRun> = {}): RemediationRun {
  return {
    id: 7, actionId: 1, actionName: 'restart-web', hostname: 'web-01', service: 'HTTP', state: 'CRITICAL',
    stateType: 'HARD', attempt: 3, receivedAt: '2026-10-14T10:00:00', startedAt: '2026-10-14T10:00:01',
    finishedAt: '2026-10-14T10:00:02', outcome: 'succeeded', reason: null, ...overrides,
  }
}

function runList(items: RemediationRun[], overrides = {}) {
  return { items, page: 1, per_page: 10, pages: 1, total: items.length, ...overrides }
}

beforeEach(() => {
  permissions = ['remediation.view', 'remediation.manage']
  Object.values(api).forEach((fn) => fn.mockReset())
  api.getActionTypes.mockResolvedValue(TYPES)
  api.listActions.mockResolvedValue([action()])
  api.listRuns.mockResolvedValue(runList([run()]))
  api.getRun.mockResolvedValue({ ...run(), output: 'recorded' })
  vi.spyOn(window, 'confirm').mockReturnValue(true)
})

// ==========================================================
// ACTIONS TAB
// ==========================================================

describe('Remediation page: actions', () => {
  it('shows the warning banner and the actions with what they cover', async () => {
    render(<RemediationPage />)
    expect(screen.getByRole('heading', { name: 'Remediation' })).toBeInTheDocument()
    expect(screen.getByText(/Actions run automatically when a service reaches a hard failure/i)).toBeInTheDocument()
    expect(await screen.findByText('restart-web')).toBeInTheDocument()
    expect(screen.getByText('web-* / HTTP')).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Enable restart-web' })).toBeChecked()
  })

  it('shows a loading state, then an empty state', async () => {
    api.listActions.mockResolvedValue([])
    render(<RemediationPage />)
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
    expect(await screen.findByText(/No actions yet/i)).toBeInTheDocument()
  })

  it('shows a load error', async () => {
    api.listActions.mockRejectedValue(new ApiError('Backend broke', 500))
    render(<RemediationPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Backend broke')
  })

  it('shows a permission message when the server says 403', async () => {
    api.listActions.mockRejectedValue(new ApiError('Forbidden', 403))
    render(<RemediationPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/do not have permission/i)
  })

  it('turns an action off with its switch, sending the current version', async () => {
    api.updateAction.mockResolvedValue(action({ enabled: false, version: 4 }))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('switch', { name: 'Enable restart-web' }))
    await waitFor(() => expect(api.updateAction).toHaveBeenCalledTimes(1))
    const [id, input, version] = api.updateAction.mock.calls[0]
    expect(id).toBe(1)
    expect(version).toBe(3)
    expect(input).toMatchObject({ name: 'restart-web', enabled: false, hostPattern: 'web-*', servicePattern: 'HTTP' })
    expect(await screen.findByRole('switch', { name: 'Enable restart-web' })).not.toBeChecked()
  })

  it('shows the server message when the switch cannot be applied', async () => {
    api.updateAction.mockRejectedValue(new ApiError('The action could not be applied: Nagios said no', 422))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('switch', { name: 'Enable restart-web' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Nagios said no')
    expect(screen.getByRole('switch', { name: 'Enable restart-web' })).toBeChecked()
  })

  it('creates an action from the form', async () => {
    api.listActions.mockResolvedValueOnce([]).mockResolvedValue([action()])
    api.createAction.mockResolvedValue(action())
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    const dialog = screen.getByRole('dialog', { name: 'Add action' })
    fireEvent.change(within(dialog).getByLabelText('Name'), { target: { value: 'restart-web' } })
    fireEvent.change(within(dialog).getByLabelText('Host pattern'), { target: { value: 'web-*' } })
    fireEvent.change(within(dialog).getByLabelText('Service pattern'), { target: { value: 'HTTP' } })
    fireEvent.change(within(dialog).getByLabelText('Cooldown (seconds)'), { target: { value: '900' } })
    fireEvent.change(within(dialog).getByLabelText('Max runs per hour'), { target: { value: '3' } })
    fireEvent.click(within(dialog).getByRole('checkbox', { name: 'Enabled' }))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    await waitFor(() => expect(api.createAction).toHaveBeenCalledTimes(1))
    expect(api.createAction).toHaveBeenCalledWith({
      name: 'restart-web', actionType: 'record_only', scopeKind: 'service', hostPattern: 'web-*',
      servicePattern: 'HTTP', parameters: {}, enabled: true, maxRunsPerHour: 3, cooldownSeconds: 900,
    })
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(await screen.findByText('restart-web')).toBeInTheDocument()
  })

  it('describes the chosen action type in the form', async () => {
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    expect(await screen.findByText('Changes nothing.')).toBeInTheDocument()
  })

  it('shows each server validation message against its own field', async () => {
    api.createAction.mockRejectedValue(
      new ApiError('Some fields are not valid.', 400, {
        fields: { name: 'An action with this name already exists.', hostPattern: 'Host pattern must be 1 to 100 letters.' },
      }),
    )
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    const dialog = screen.getByRole('dialog', { name: 'Add action' })
    fireEvent.change(within(dialog).getByLabelText('Name'), { target: { value: 'restart-web' } })
    fireEvent.change(within(dialog).getByLabelText('Host pattern'), { target: { value: 'web-*' } })
    fireEvent.change(within(dialog).getByLabelText('Service pattern'), { target: { value: 'HTTP' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    const nameField = within(dialog).getByLabelText('Name')
    expect(await within(dialog).findByText('An action with this name already exists.')).toBeInTheDocument()
    expect(nameField).toHaveAccessibleDescription('An action with this name already exists.')
    expect(within(dialog).getByLabelText('Host pattern')).toHaveAccessibleDescription(/Host pattern must be/)
    expect(within(dialog).getByLabelText('Service pattern')).not.toHaveAccessibleDescription(/\w/)
    expect(screen.getByRole('dialog', { name: 'Add action' })).toBeInTheDocument()
  })

  it('hides the service pattern for a host action and sends null', async () => {
    api.createAction.mockResolvedValue(action({ scopeKind: 'host', servicePattern: null }))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    const dialog = screen.getByRole('dialog', { name: 'Add action' })
    fireEvent.change(within(dialog).getByLabelText('Scope'), { target: { value: 'host' } })
    expect(within(dialog).queryByLabelText('Service pattern')).not.toBeInTheDocument()
    fireEvent.change(within(dialog).getByLabelText('Name'), { target: { value: 'host-rule' } })
    fireEvent.change(within(dialog).getByLabelText('Host pattern'), { target: { value: 'web-01' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    await waitFor(() => expect(api.createAction).toHaveBeenCalled())
    expect(api.createAction.mock.calls[0][0]).toMatchObject({ scopeKind: 'host', servicePattern: null })
  })

  it('edits an action with its current values and version', async () => {
    api.updateAction.mockResolvedValue(action({ cooldownSeconds: 900, version: 4 }))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Edit restart-web' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit action' })
    expect(within(dialog).getByLabelText('Name')).toHaveValue('restart-web')
    expect(within(dialog).getByLabelText('Cooldown (seconds)')).toHaveValue(600)
    fireEvent.change(within(dialog).getByLabelText('Cooldown (seconds)'), { target: { value: '900' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    await waitFor(() => expect(api.updateAction).toHaveBeenCalled())
    expect(api.updateAction.mock.calls[0][0]).toBe(1)
    expect(api.updateAction.mock.calls[0][1]).toMatchObject({ cooldownSeconds: 900 })
    expect(api.updateAction.mock.calls[0][2]).toBe(3)
  })

  it('offers a reload when someone else changed the action (409)', async () => {
    api.updateAction.mockRejectedValue(new ApiError('This action was changed by someone else. Reload and try again.', 409))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Edit restart-web' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit action' })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    const alert = await within(dialog).findByRole('alert')
    expect(alert).toHaveTextContent(/changed by someone else/i)
    fireEvent.click(within(alert).getByRole('button', { name: /Reload/i }))
    await waitFor(() => expect(api.listActions).toHaveBeenCalledTimes(2))
  })

  it('shows the server message when Nagios rejects the config (422)', async () => {
    api.updateAction.mockRejectedValue(new ApiError('The action could not be applied: bad config', 422))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Edit restart-web' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit action' })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    expect(await within(dialog).findByRole('alert')).toHaveTextContent('bad config')
  })

  it('deletes an action only after confirmation', async () => {
    api.deleteAction.mockResolvedValue(null)
    render(<RemediationPage />)
    const confirm = vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true)
    fireEvent.click(await screen.findByRole('button', { name: 'Delete restart-web' }))
    expect(api.deleteAction).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Delete restart-web' }))
    await waitFor(() => expect(api.deleteAction).toHaveBeenCalledWith(1))
    expect(confirm).toHaveBeenCalledTimes(2)
  })
})

// ==========================================================
// VIEW-ONLY USERS
// ==========================================================

describe('Remediation page: view permission only', () => {
  beforeEach(() => {
    permissions = ['remediation.view']
  })

  it('lists actions but offers no way to change them', async () => {
    render(<RemediationPage />)
    expect(await screen.findByText('restart-web')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Add action' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Edit restart-web' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Delete restart-web' })).not.toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Enable restart-web' })).toBeDisabled()
  })
})

// ==========================================================
// RUN LOG TAB
// ==========================================================

describe('Remediation page: run log', () => {
  async function openRunLog() {
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('tab', { name: 'Run log' }))
  }

  it('lists runs with host, service, state and outcome', async () => {
    await openRunLog()
    expect(await screen.findByText('web-01')).toBeInTheDocument()
    const row = screen.getByText('web-01').closest('tr') as HTMLElement
    expect(within(row).getByText('restart-web')).toBeInTheDocument()
    expect(within(row).getByText('HTTP')).toBeInTheDocument()
    expect(within(row).getByText('Succeeded')).toBeInTheDocument()
  })

  it('shows why a skipped run was skipped', async () => {
    api.listRuns.mockResolvedValue(runList([
      run({ id: 8, outcome: 'skipped_cooldown', reason: 'Within the 600 second cooldown since the last run for this host and service.' }),
    ]))
    await openRunLog()
    expect(await screen.findByText('Skipped (cooldown)')).toBeInTheDocument()
    expect(screen.getByText(/Within the 600 second cooldown/)).toBeInTheDocument()
  })

  it('shows empty and error states', async () => {
    api.listRuns.mockResolvedValue(runList([]))
    await openRunLog()
    expect(await screen.findByText(/No runs yet/i)).toBeInTheDocument()
  })

  it('shows a load error for the log', async () => {
    api.listRuns.mockRejectedValue(new ApiError('Log broke', 500))
    await openRunLog()
    expect(await screen.findByRole('alert')).toHaveTextContent('Log broke')
  })

  it('filters by outcome and host and goes back to the first page', async () => {
    await openRunLog()
    await screen.findByText('web-01')
    fireEvent.change(screen.getByLabelText('Outcome'), { target: { value: 'skipped_cooldown' } })
    await waitFor(() => expect(api.listRuns).toHaveBeenLastCalledWith(expect.objectContaining({ outcome: 'skipped_cooldown', page: 1 })))
    fireEvent.change(screen.getByLabelText('Host'), { target: { value: 'web-01' } })
    await waitFor(() => expect(api.listRuns).toHaveBeenLastCalledWith(expect.objectContaining({ outcome: 'skipped_cooldown', host: 'web-01' })))
  })

  it('filters by action and date range', async () => {
    await openRunLog()
    await screen.findByText('web-01')
    fireEvent.change(screen.getByLabelText('Action'), { target: { value: '1' } })
    await waitFor(() => expect(api.listRuns).toHaveBeenLastCalledWith(expect.objectContaining({ action: 1 })))
    fireEvent.change(screen.getByLabelText('From'), { target: { value: '2026-10-01' } })
    fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-10-14' } })
    await waitFor(() => expect(api.listRuns).toHaveBeenLastCalledWith(expect.objectContaining({ from: '2026-10-01', to: '2026-10-14' })))
  })

  it('pages through the log', async () => {
    api.listRuns.mockResolvedValue(runList([run()], { pages: 3, total: 25 }))
    await openRunLog()
    await screen.findByText('web-01')
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    await waitFor(() => expect(api.listRuns).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })))
  })

  it('opens a run to see its details and output', async () => {
    await openRunLog()
    fireEvent.click(await screen.findByRole('button', { name: 'View run 7' }))
    const drawer = await screen.findByRole('dialog', { name: 'Run 7' })
    expect(api.getRun).toHaveBeenCalledWith(7)
    expect(await within(drawer).findByText('recorded')).toBeInTheDocument()
    expect(within(drawer).getByText('web-01')).toBeInTheDocument()
    fireEvent.click(within(drawer).getByRole('button', { name: 'Close' }))
    expect(screen.queryByRole('dialog', { name: 'Run 7' })).not.toBeInTheDocument()
  })

  it('shows an error inside the drawer when a run cannot be loaded', async () => {
    api.getRun.mockRejectedValue(new ApiError('Run not found.', 404))
    await openRunLog()
    fireEvent.click(await screen.findByRole('button', { name: 'View run 7' }))
    const drawer = await screen.findByRole('dialog', { name: 'Run 7' })
    expect(await within(drawer).findByRole('alert')).toHaveTextContent('Run not found.')
  })

  it('is available to a user who can only view', async () => {
    permissions = ['remediation.view']
    await openRunLog()
    expect(await screen.findByText('web-01')).toBeInTheDocument()
  })
})
