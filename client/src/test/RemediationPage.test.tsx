import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { RemediationPage } from '../pages/RemediationPage'
import type { RemediationAction, RemediationHealth, RemediationRun } from '../types/remediation'

const api = vi.hoisted(() => ({
  getActionTypes: vi.fn(),
  getTargets: vi.fn(),
  listActions: vi.fn(),
  createAction: vi.fn(),
  updateAction: vi.fn(),
  deleteAction: vi.fn(),
  listRuns: vi.fn(),
  getRun: vi.fn(),
  getHealth: vi.fn(),
  getSettings: vi.fn(),
  updateSettings: vi.fn(),
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
    runWhenAcknowledged: false, notifyOn: ['failed', 'capped', 'repeated'], version: 3, updatedAt: '2026-10-14T10:00:00', updatedBy: 1, ...overrides,
  }
}

function run(overrides: Partial<RemediationRun> = {}): RemediationRun {
  return {
    id: 7, actionId: 1, actionName: 'restart-web', hostname: 'web-01', service: 'HTTP', state: 'CRITICAL',
    stateType: 'HARD', attempt: 3, receivedAt: '2026-10-14T10:00:00', startedAt: '2026-10-14T10:00:01',
    finishedAt: '2026-10-14T10:00:02', outcome: 'succeeded', reason: null, notifyKind: null, notifyState: null,
    notifyAttempts: 0, notifyError: null, notifyAt: null, ...overrides,
  }
}

function health(overrides: Partial<RemediationHealth> = {}): RemediationHealth {
  return {
    lastTickAt: '2026-10-14T10:00:00', lastError: null, stalled: false, backlog: 2, oldestSpoolAgeSeconds: 30,
    runsLast24h: 5, capsHitLast24h: 1, skippedLast24h: 3, droppedTotal: 0, droppedAt: null, ...overrides,
  }
}

function runList(items: RemediationRun[], overrides = {}) {
  return { items, page: 1, per_page: 10, pages: 1, total: items.length, ...overrides }
}

beforeEach(() => {
  permissions = ['remediation.view', 'remediation.manage']
  Object.values(api).forEach((fn) => fn.mockReset())
  api.getActionTypes.mockResolvedValue(TYPES)
  api.getTargets.mockResolvedValue([{ hostname: 'web-01', services: ['HTTP', 'SSH'] }, { hostname: 'db-01', services: ['MySQL'] }])
  api.listActions.mockResolvedValue([action()])
  api.listRuns.mockResolvedValue(runList([run()]))
  api.getRun.mockResolvedValue({ ...run(), output: 'recorded' })
  api.getHealth.mockResolvedValue(health())
  api.getSettings.mockResolvedValue({ enabled: true, retentionDays: 90, repeatCount: 3, repeatWindowHours: 24 })
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
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: 'web-*' } })
    fireEvent.change(within(dialog).getByLabelText('Service'), { target: { value: 'HTTP' } })
    fireEvent.change(within(dialog).getByLabelText('Cooldown (seconds)'), { target: { value: '900' } })
    fireEvent.change(within(dialog).getByLabelText('Max runs per hour'), { target: { value: '3' } })
    fireEvent.click(within(dialog).getByRole('checkbox', { name: 'Enabled' }))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    await waitFor(() => expect(api.createAction).toHaveBeenCalledTimes(1))
    expect(api.createAction).toHaveBeenCalledWith({
      name: 'restart-web', actionType: 'record_only', scopeKind: 'service', hostPattern: 'web-*',
      servicePattern: 'HTTP', parameters: {}, enabled: true, maxRunsPerHour: 3, cooldownSeconds: 900,
      runWhenAcknowledged: false, notifyOn: ['failed', 'capped', 'repeated'],
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
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: 'web-*' } })
    fireEvent.change(within(dialog).getByLabelText('Service'), { target: { value: 'HTTP' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    const nameField = within(dialog).getByLabelText('Name')
    expect(await within(dialog).findByText('An action with this name already exists.')).toBeInTheDocument()
    expect(nameField).toHaveAccessibleDescription('An action with this name already exists.')
    expect(within(dialog).getByLabelText('Device')).toHaveAccessibleDescription(/Host pattern must be/)
    expect(within(dialog).getByLabelText('Service')).not.toHaveAccessibleDescription(/\w/)
    expect(screen.getByRole('dialog', { name: 'Add action' })).toBeInTheDocument()
  })

  it('hides the service pattern for a host action and sends null', async () => {
    api.createAction.mockResolvedValue(action({ scopeKind: 'host', servicePattern: null }))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    const dialog = screen.getByRole('dialog', { name: 'Add action' })
    fireEvent.change(within(dialog).getByLabelText('Scope'), { target: { value: 'host' } })
    expect(within(dialog).queryByLabelText('Service')).not.toBeInTheDocument()
    fireEvent.change(within(dialog).getByLabelText('Name'), { target: { value: 'host-rule' } })
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: 'web-01' } })
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

// ==========================================================
// SAFETY CONTROLS (issue #155)
// ==========================================================

describe('Remediation page: health and kill switch', () => {
  const panel = async () => within(await screen.findByRole('region', { name: 'Automatic recovery status' }))

  it('shows the live health values', async () => {
    render(<RemediationPage />)
    const status = await panel()
    expect(await status.findByText('Events waiting')).toBeInTheDocument()
    expect(status.getByTestId('health-backlog')).toHaveTextContent('2')
    expect(status.getByTestId('health-runs')).toHaveTextContent('5')
    expect(status.getByTestId('health-caps')).toHaveTextContent('1')
    expect(status.getByTestId('health-skipped')).toHaveTextContent('3')
    expect(screen.queryByText(/stopped checking in/i)).not.toBeInTheDocument()
  })

  it('shows a prominent banner when the consumer is stalled', async () => {
    api.getHealth.mockResolvedValue(health({ stalled: true }))
    render(<RemediationPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/stopped checking in/i)
  })

  it("shows the consumer's last error and any dropped events", async () => {
    api.getHealth.mockResolvedValue(health({ lastError: 'The spool folder could not be read.', droppedTotal: 4 }))
    render(<RemediationPage />)
    const status = await panel()
    expect(await status.findByText('The spool folder could not be read.')).toBeInTheDocument()
    expect(status.getByTestId('health-dropped')).toHaveTextContent('4')
  })

  it('says so when the health cannot be loaded, without hiding the actions', async () => {
    api.getHealth.mockRejectedValue(new ApiError('Boom', 500))
    render(<RemediationPage />)
    expect(await screen.findByText('restart-web')).toBeInTheDocument()
    expect(await screen.findByText(/Unable to load the health of automatic recovery/i)).toBeInTheDocument()
  })

  it('shows a loading state before the health arrives', async () => {
    api.getHealth.mockReturnValue(new Promise(() => {}))
    render(<RemediationPage />)
    expect(await screen.findByText(/Checking status/i)).toBeInTheDocument()
  })

  it('asks for confirmation before stopping all automatic recovery, then saves it', async () => {
    api.updateSettings.mockResolvedValue({ enabled: false, retentionDays: 90 })
    render(<RemediationPage />)
    const toggle = await screen.findByRole('switch', { name: 'Automatic recovery' })
    expect(toggle).toBeChecked()
    fireEvent.click(toggle)
    expect(window.confirm).toHaveBeenCalledWith(expect.stringMatching(/stops for every action/i))
    await waitFor(() => expect(api.updateSettings).toHaveBeenCalledWith({ enabled: false }))
    expect(await screen.findByRole('switch', { name: 'Automatic recovery' })).not.toBeChecked()
  })

  it('changes nothing when the confirmation is declined', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('switch', { name: 'Automatic recovery' }))
    expect(api.updateSettings).not.toHaveBeenCalled()
    expect(screen.getByRole('switch', { name: 'Automatic recovery' })).toBeChecked()
  })

  it('shows the saved state after a reload and marks each enabled action as paused', async () => {
    api.getSettings.mockResolvedValue({ enabled: false, retentionDays: 90 })
    render(<RemediationPage />)
    expect(await screen.findByRole('switch', { name: 'Automatic recovery' })).not.toBeChecked()
    const row = (await screen.findByText('restart-web')).closest('tr') as HTMLElement
    expect(within(row).getByText(/Paused by the kill switch/i)).toBeInTheDocument()
  })

  it('turning it back on also asks first', async () => {
    api.getSettings.mockResolvedValue({ enabled: false, retentionDays: 90 })
    api.updateSettings.mockResolvedValue({ enabled: true, retentionDays: 90 })
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('switch', { name: 'Automatic recovery' }))
    expect(window.confirm).toHaveBeenCalledWith(expect.stringMatching(/resume/i))
    await waitFor(() => expect(api.updateSettings).toHaveBeenCalledWith({ enabled: true }))
  })

  it('keeps the old state and shows the message when saving fails', async () => {
    api.updateSettings.mockRejectedValue(new ApiError('You do not have permission', 403))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('switch', { name: 'Automatic recovery' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('You do not have permission')
    expect(screen.getByRole('switch', { name: 'Automatic recovery' })).toBeChecked()
  })

  it('lets a view-only user see the switch but not change it', async () => {
    permissions = ['remediation.view']
    render(<RemediationPage />)
    expect(await screen.findByRole('switch', { name: 'Automatic recovery' })).toBeDisabled()
  })

  it('shows a permission message when the settings are forbidden', async () => {
    api.getSettings.mockRejectedValue(new ApiError('Forbidden', 403))
    render(<RemediationPage />)
    expect(await screen.findByText(/do not have permission to view the kill switch/i)).toBeInTheDocument()
  })
})

describe('Remediation page: run when acknowledged', () => {
  it('offers the option with help text, off by default, and sends it', async () => {
    api.createAction.mockResolvedValue(action())
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    const dialog = screen.getByRole('dialog', { name: 'Add action' })
    const box = within(dialog).getByRole('checkbox', { name: 'Run when acknowledged' })
    expect(box).not.toBeChecked()
    expect(within(dialog).getByText(/skipped when an operator has already acknowledged/i)).toBeInTheDocument()
    fireEvent.click(box)
    fireEvent.change(within(dialog).getByLabelText('Name'), { target: { value: 'ack-ok' } })
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: 'web-01' } })
    fireEvent.change(within(dialog).getByLabelText('Service'), { target: { value: 'HTTP' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    await waitFor(() => expect(api.createAction).toHaveBeenCalled())
    expect(api.createAction.mock.calls[0][0]).toMatchObject({ runWhenAcknowledged: true })
  })

  it('shows the saved value when editing', async () => {
    api.listActions.mockResolvedValue([action({ runWhenAcknowledged: true })])
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Edit restart-web' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit action' })
    expect(within(dialog).getByRole('checkbox', { name: 'Run when acknowledged' })).toBeChecked()
  })

  it('keeps the value when the enable switch is used', async () => {
    api.listActions.mockResolvedValue([action({ runWhenAcknowledged: true })])
    api.updateAction.mockResolvedValue(action({ enabled: false, runWhenAcknowledged: true, version: 4 }))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('switch', { name: 'Enable restart-web' }))
    await waitFor(() => expect(api.updateAction).toHaveBeenCalled())
    expect(api.updateAction.mock.calls[0][1]).toMatchObject({ runWhenAcknowledged: true })
  })
})

describe('Remediation page: skip reasons in the run log', () => {
  it('shows every new skip outcome with its reason and offers them as filters', async () => {
    api.listRuns.mockResolvedValue(runList([
      run({ id: 11, outcome: 'skipped_kill_switch', reason: 'Automatic recovery is switched off (kill switch).' }),
      run({ id: 12, outcome: 'skipped_maintenance', reason: 'Maintenance Mode is on.', hostname: 'web-02' }),
      run({ id: 13, outcome: 'skipped_downtime', reason: 'The problem is in scheduled downtime.', hostname: 'web-03' }),
      run({ id: 14, outcome: 'skipped_acknowledged', reason: 'An operator has already acknowledged this problem.', hostname: 'web-04' }),
    ]))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('tab', { name: 'Run log' }))
    expect(await screen.findAllByText('Skipped (kill switch)')).not.toHaveLength(0)
    expect(screen.getAllByText('Skipped (maintenance)')).not.toHaveLength(0)
    expect(screen.getAllByText('Skipped (downtime)')).not.toHaveLength(0)
    expect(screen.getAllByText('Skipped (acknowledged)')).not.toHaveLength(0)
    expect(screen.getByText(/switched off \(kill switch\)/)).toBeInTheDocument()
    expect(screen.getByText('Maintenance Mode is on.')).toBeInTheDocument()
    const filter = screen.getByLabelText('Outcome')
    expect(within(filter).getByRole('option', { name: 'Skipped (kill switch)' })).toBeInTheDocument()
  })
})


describe('Remediation page: operator notification in the run log', () => {
  async function openRunLog() {
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('tab', { name: 'Run log' }))
  }

  it('says "Not required" for a run that needed no notification', async () => {
    await openRunLog()
    const row = (await screen.findByText('web-01')).closest('tr') as HTMLElement
    expect(within(row).getByText('Not required')).toBeInTheDocument()
  })

  it('says the operator was notified when the notification was sent', async () => {
    api.listRuns.mockResolvedValue(runList([
      run({ outcome: 'failed', notifyKind: 'failed', notifyState: 'sent', notifyAttempts: 1, notifyAt: '2026-10-14T10:00:03' }),
    ]))
    await openRunLog()
    expect(await screen.findByText('Operator notified')).toBeInTheDocument()
  })

  it('shows a notification that is still waiting to be sent', async () => {
    api.listRuns.mockResolvedValue(runList([
      run({ outcome: 'failed', notifyKind: 'failed', notifyState: 'pending', notifyAttempts: 1, notifyError: 'The Nagios command pipe was not found.' }),
    ]))
    await openRunLog()
    expect(await screen.findByText('Notification pending')).toBeInTheDocument()
  })

  it('shows a failed notification with its error', async () => {
    api.listRuns.mockResolvedValue(runList([
      run({ outcome: 'timed_out', notifyKind: 'failed', notifyState: 'failed', notifyAttempts: 3, notifyError: 'The Nagios command pipe was not found.' }),
    ]))
    await openRunLog()
    const row = (await screen.findByText('web-01')).closest('tr') as HTMLElement
    expect(within(row).getByText('Notification failed')).toBeInTheDocument()
    expect(within(row).getByText('The Nagios command pipe was not found.')).toBeInTheDocument()
  })

  it('shows the notification details in the run drawer', async () => {
    const detail = run({
      outcome: 'skipped_hourly_cap', notifyKind: 'capped', notifyState: 'failed', notifyAttempts: 3,
      notifyError: 'The Nagios command pipe could not be written.', notifyAt: null,
    })
    api.listRuns.mockResolvedValue(runList([detail]))
    api.getRun.mockResolvedValue({ ...detail, output: null })
    await openRunLog()
    fireEvent.click(await screen.findByRole('button', { name: 'View run 7' }))
    const drawer = await screen.findByRole('dialog', { name: 'Run 7' })
    expect(await within(drawer).findByText('Notification failed')).toBeInTheDocument()
    expect(within(drawer).getByText('Stopped by its limits')).toBeInTheDocument()
    expect(within(drawer).getByText('The Nagios command pipe could not be written.')).toBeInTheDocument()
    expect(within(drawer).getByText('3')).toBeInTheDocument()
  })

  it('shows "Not required" in the drawer when nothing was due', async () => {
    await openRunLog()
    fireEvent.click(await screen.findByRole('button', { name: 'View run 7' }))
    const drawer = await screen.findByRole('dialog', { name: 'Run 7' })
    expect(await within(drawer).findByText('Not required')).toBeInTheDocument()
  })
})


describe('Remediation page: notify the operator (action form)', () => {
  it('offers the three kinds with help text, all on by default, and sends them', async () => {
    api.createAction.mockResolvedValue(action())
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    const dialog = screen.getByRole('dialog', { name: 'Add action' })
    const group = within(dialog).getByRole('group', { name: 'Tell the operator when' })
    for (const name of ['The action fails', 'The action is stopped by its limits', 'It keeps recovering the same service']) {
      expect(within(group).getByRole('checkbox', { name })).toBeChecked()
    }
    expect(within(dialog).getByText(/Nagios sends the message to the contacts of that service/i)).toBeInTheDocument()
    fireEvent.change(within(dialog).getByLabelText('Name'), { target: { value: 'notify-ok' } })
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: 'web-01' } })
    fireEvent.change(within(dialog).getByLabelText('Service'), { target: { value: 'HTTP' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    await waitFor(() => expect(api.createAction).toHaveBeenCalled())
    expect(api.createAction.mock.calls[0][0]).toMatchObject({ notifyOn: ['failed', 'capped', 'repeated'] })
  })

  it('sends only the kinds that stay ticked, in a fixed order', async () => {
    api.createAction.mockResolvedValue(action())
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    const dialog = screen.getByRole('dialog', { name: 'Add action' })
    fireEvent.click(within(dialog).getByRole('checkbox', { name: 'The action fails' }))
    fireEvent.change(within(dialog).getByLabelText('Name'), { target: { value: 'quiet' } })
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: 'web-01' } })
    fireEvent.change(within(dialog).getByLabelText('Service'), { target: { value: 'HTTP' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    await waitFor(() => expect(api.createAction).toHaveBeenCalled())
    expect(api.createAction.mock.calls[0][0]).toMatchObject({ notifyOn: ['capped', 'repeated'] })
  })

  it('can turn every kind off', async () => {
    api.listActions.mockResolvedValue([action({ notifyOn: ['failed'] })])
    api.updateAction.mockResolvedValue(action({ notifyOn: [] }))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Edit restart-web' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit action' })
    fireEvent.click(within(dialog).getByRole('checkbox', { name: 'The action fails' }))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    await waitFor(() => expect(api.updateAction).toHaveBeenCalled())
    expect(api.updateAction.mock.calls[0][1]).toMatchObject({ notifyOn: [] })
  })

  it('shows the saved choice when editing', async () => {
    api.listActions.mockResolvedValue([action({ notifyOn: ['capped'] })])
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Edit restart-web' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit action' })
    expect(within(dialog).getByRole('checkbox', { name: 'The action fails' })).not.toBeChecked()
    expect(within(dialog).getByRole('checkbox', { name: 'The action is stopped by its limits' })).toBeChecked()
    expect(within(dialog).getByRole('checkbox', { name: 'It keeps recovering the same service' })).not.toBeChecked()
  })

  it('keeps the choice when the enable switch is used', async () => {
    api.listActions.mockResolvedValue([action({ notifyOn: ['failed'] })])
    api.updateAction.mockResolvedValue(action({ enabled: false, notifyOn: ['failed'], version: 4 }))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('switch', { name: 'Enable restart-web' }))
    await waitFor(() => expect(api.updateAction).toHaveBeenCalled())
    expect(api.updateAction.mock.calls[0][1]).toMatchObject({ notifyOn: ['failed'] })
  })

  it('shows the server message against the field', async () => {
    api.createAction.mockRejectedValue(new ApiError('Some fields are not valid.', 400, { fields: { notifyOn: 'Notify on must be a list of failed, capped or repeated.' } }))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Add action' }))
    const dialog = screen.getByRole('dialog', { name: 'Add action' })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save action' }))
    expect(await within(dialog).findByText(/Notify on must be a list/)).toBeInTheDocument()
  })
})

describe('Remediation page: repeat recovery limits', () => {
  it('shows the saved count and window', async () => {
    api.getSettings.mockResolvedValue({ enabled: true, retentionDays: 90, repeatCount: 5, repeatWindowHours: 48 })
    render(<RemediationPage />)
    // The fields exist before the saved settings arrive, so wait for the values themselves.
    await waitFor(() => expect(screen.getByLabelText('Repeat count')).toHaveValue(5))
    expect(screen.getByLabelText('Repeat window (hours)')).toHaveValue(48)
    expect(screen.getByText(/recovers the same service this many times/i)).toBeInTheDocument()
  })

  it('saves both values', async () => {
    api.updateSettings.mockResolvedValue({ enabled: true, retentionDays: 90, repeatCount: 4, repeatWindowHours: 12 })
    render(<RemediationPage />)
    fireEvent.change(await screen.findByLabelText('Repeat count'), { target: { value: '4' } })
    fireEvent.change(screen.getByLabelText('Repeat window (hours)'), { target: { value: '12' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save repeat limits' }))
    await waitFor(() => expect(api.updateSettings).toHaveBeenCalledWith({ repeatCount: 4, repeatWindowHours: 12 }))
    expect(await screen.findByText('Repeat limits saved.')).toBeInTheDocument()
  })

  it('shows the server message when saving fails and keeps the typed values', async () => {
    api.updateSettings.mockRejectedValue(new ApiError('Repeat count must be a whole number from 2 to 20.', 400))
    render(<RemediationPage />)
    fireEvent.change(await screen.findByLabelText('Repeat count'), { target: { value: '99' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save repeat limits' }))
    expect(await screen.findByText(/Repeat count must be a whole number from 2 to 20/)).toBeInTheDocument()
    expect(screen.getByLabelText('Repeat count')).toHaveValue(99)
  })

  it('is read-only for a user who can only view', async () => {
    permissions = ['remediation.view']
    render(<RemediationPage />)
    expect(await screen.findByLabelText('Repeat count')).toBeDisabled()
    expect(screen.getByLabelText('Repeat window (hours)')).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Save repeat limits' })).not.toBeInTheDocument()
  })

  it('shows nothing to edit while the settings could not be loaded', async () => {
    api.getSettings.mockRejectedValue(new ApiError('Forbidden', 403))
    render(<RemediationPage />)
    expect(await screen.findByText(/do not have permission to view the kill switch/i)).toBeInTheDocument()
    expect(screen.queryByLabelText('Repeat count')).not.toBeInTheDocument()
  })
})

describe('Remediation page: opened from a service row badge', () => {
  afterEach(() => window.history.pushState({}, '', '/'))

  it('opens the run log and that run when the address names one', async () => {
    window.history.pushState({}, '', '/remediation?run=7')
    render(<RemediationPage />)
    expect(await screen.findByRole('dialog', { name: 'Run 7' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Run log' })).toHaveAttribute('aria-selected', 'true')
    await waitFor(() => expect(api.getRun).toHaveBeenCalledWith(7))
  })

  it('ignores an address that does not name a whole number', async () => {
    window.history.pushState({}, '', '/remediation?run=abc')
    render(<RemediationPage />)
    expect(await screen.findByRole('tab', { name: 'Actions' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('opens nothing without the parameter', async () => {
    render(<RemediationPage />)
    expect(await screen.findByRole('tab', { name: 'Actions' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

// ==========================================================
// DEVICE AND SERVICE SUGGESTIONS
// ==========================================================

describe('device and service suggestions', () => {
  const options = (dialog: HTMLElement, id: string) =>
    Array.from(dialog.querySelectorAll(`#${id} option`)).map((o) => (o as HTMLOptionElement).value)

  it('suggests devices, and the services of the device typed or matched by a pattern', async () => {
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: /add action/i }))
    const dialog = await screen.findByRole('dialog')
    await waitFor(() => expect(options(dialog, 'remediation-device-options')).toEqual(['web-01', 'db-01']))
    expect(options(dialog, 'remediation-service-options')).toEqual([])
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: 'web-01' } })
    expect(options(dialog, 'remediation-service-options')).toEqual(['HTTP', 'SSH'])
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: '*-01' } })
    expect(options(dialog, 'remediation-service-options')).toEqual(['HTTP', 'MySQL', 'SSH'])
  })

  it('still lets a pattern be typed when the suggestions cannot load', async () => {
    api.getTargets.mockRejectedValue(new Error('down'))
    render(<RemediationPage />)
    fireEvent.click(await screen.findByRole('button', { name: /add action/i }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Device'), { target: { value: 'web-*' } })
    expect(within(dialog).getByLabelText('Device')).toHaveValue('web-*')
  })
})
