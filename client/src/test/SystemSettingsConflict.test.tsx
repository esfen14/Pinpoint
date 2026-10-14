import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { GeneralSettings } from '../components/settings/GeneralSettings'
import { SystemSettings } from '../components/settings/SystemSettings'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  DEFAULT_SYSTEM_SETTINGS,
  SystemSettingsProvider,
  useSystemSettings,
} from '../contexts/SystemSettingsContext'

// A tiny fake backend for /api/system (versioned) and /api/user/preferences.
const PREFERENCE_KEYS = [
  'theme', 'timeZone', 'dateTimeFormat', 'systemFont',
  'systemFontSize', 'dashboardLayout', 'dashboardRefreshRate',
]

let server: Record<string, unknown>
let systemPuts: Record<string, unknown>[]
let applyError: string | null

function splitSystem(all: Record<string, unknown>) {
  const system: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(all)) {
    if (!PREFERENCE_KEYS.includes(key)) system[key] = value
  }
  return system
}

function respond(status: number, body: unknown) {
  return Promise.resolve({
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
  })
}

const fetchMock = vi.fn((url: string, init?: RequestInit) => {
  const method = init?.method ?? 'GET'
  const body = init?.body ? JSON.parse(String(init.body)) : undefined

  if (url === '/api/system' && method === 'GET') {
    return respond(200, { success: true, data: splitSystem(server) })
  }
  if (url === '/api/system' && method === 'PUT') {
    systemPuts.push(body)
    if (applyError) return respond(422, { success: false, message: applyError })
    if (body.version !== server.version) {
      return respond(409, { success: false, message: 'conflict' })
    }
    server = { ...server, ...splitSystem(body), version: (server.version as number) + 1 }
    return respond(200, { success: true, data: splitSystem(server) })
  }
  if (url === '/api/user/preferences') {
    return respond(200, Object.fromEntries(PREFERENCE_KEYS.map((key) => [key, server[key]])))
  }
  return respond(404, {})
})

// Someone else saving from another tab/admin.
function changeOnServer(updates: Record<string, unknown>) {
  server = { ...server, ...updates, version: (server.version as number) + 1 }
}

let api: ReturnType<typeof useSystemSettings>

function Probe() {
  // Test-only: expose the hook result to assertions outside the render.
  // eslint-disable-next-line react-hooks/globals
  api = useSystemSettings()
  return (
    <div>
      <span data-testid="timeout">{api.settings.sessionTimeout}</span>
      <span data-testid="scan">{api.settings.scanFrequency}</span>
      <span data-testid="error">{api.saveError ?? ''}</span>
    </div>
  )
}

async function renderLoaded() {
  render(
    <SystemSettingsProvider>
      <Probe />
    </SystemSettingsProvider>,
  )
  await waitFor(() => expect(api.isLoading).toBe(false))
}

async function save() {
  await act(async () => {
    await api.saveSettings().catch(() => {})
  })
}

describe('SystemSettingsProvider conflict handling', () => {
  beforeEach(() => {
    localStorage.clear()
    server = { ...DEFAULT_SYSTEM_SETTINGS, version: 1 }
    systemPuts = []
    applyError = null
    fetchMock.mockClear()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('saves check interval as a system setting without changing per-user refresh', async () => {
    await renderLoaded()
    act(() => api.updateSettings({ checkInterval: 2 }))
    await save()
    expect(systemPuts[0].checkInterval).toBe(2)
    expect(systemPuts[0].dashboardRefreshRate).toBe(5)
    expect(api.settings.dashboardRefreshRate).toBe(5)
  })

  it('shows the dynamic refresh hint and system check interval without changing personal rate', async () => {
    server.checkInterval = 2
    render(<SystemSettingsProvider><GeneralSettings /><SystemSettings /></SystemSettingsProvider>)
    await waitFor(() => expect(screen.getByText(/Nagios checks every 2 minutes/)).toBeInTheDocument())
    expect(screen.getByText('Check interval')).toBeInTheDocument()
    expect(server.dashboardRefreshRate).toBe(5)
  })

  it('shows a Nagios apply failure instead of treating it as a version conflict', async () => {
    await renderLoaded()
    applyError = 'Check interval could not be applied: Nagios reload failed'
    act(() => api.updateSettings({ checkInterval: 2 }))
    await save()
    expect(screen.getByTestId('error')).toHaveTextContent('Nagios reload failed')
    expect(systemPuts).toHaveLength(1)
  })

  it('saves normally when nothing changed elsewhere', async () => {
    await renderLoaded()

    act(() => api.updateSettings({ sessionTimeout: 60 }))
    await save()

    expect(systemPuts).toHaveLength(1)
    expect(server.sessionTimeout).toBe(60)
    expect(screen.getByTestId('error')).toHaveTextContent('')
  })

  it('keeps both changes when someone else edited a different field', async () => {
    await renderLoaded()
    changeOnServer({ scanFrequency: 12 })

    act(() => api.updateSettings({ sessionTimeout: 60 }))
    await save()

    expect(systemPuts).toHaveLength(2)
    expect(server.sessionTimeout).toBe(60)
    expect(server.scanFrequency).toBe(12)
    expect(screen.getByTestId('scan')).toHaveTextContent('12')
    expect(screen.getByTestId('error')).toHaveTextContent('')
  })

  it('reports a conflict on the same field, then keeps the user value on a second save', async () => {
    await renderLoaded()
    changeOnServer({ sessionTimeout: 15 })

    act(() => api.updateSettings({ sessionTimeout: 60 }))
    await save()

    expect(server.sessionTimeout).toBe(15)
    expect(screen.getByTestId('error')).toHaveTextContent(
      'Session Timeout was also changed by someone else',
    )
    expect(screen.getByTestId('timeout')).toHaveTextContent('60')

    await save()

    expect(server.sessionTimeout).toBe(60)
    expect(screen.getByTestId('error')).toHaveTextContent('')
  })

  it('refreshes on focus and keeps unsaved edits', async () => {
    await renderLoaded()
    act(() => api.updateSettings({ sessionTimeout: 60 }))
    changeOnServer({ scanFrequency: 3 })

    await act(async () => {
      window.dispatchEvent(new Event('focus'))
    })

    await waitFor(() => expect(screen.getByTestId('scan')).toHaveTextContent('3'))
    expect(screen.getByTestId('timeout')).toHaveTextContent('60')
    expect(api.savedSettings.version).toBe(2)

    await save()

    expect(systemPuts).toHaveLength(1)
    expect(server.sessionTimeout).toBe(60)
    expect(server.scanFrequency).toBe(3)
  })
})

describe('Check timing controls (retry interval and maximum check attempts)', () => {
  beforeEach(() => {
    localStorage.clear()
    server = { ...DEFAULT_SYSTEM_SETTINGS, version: 1 }
    systemPuts = []
    applyError = null
    fetchMock.mockClear()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  // The labels are not linked to their selects, so find the select inside the label's block.
  function selectFor(label: string) {
    const block = screen.getByText(label).closest('div')
    const select = block?.querySelector('select')
    if (!select) throw new Error(`no select for ${label}`)
    return select as HTMLSelectElement
  }

  async function renderControls() {
    render(<SystemSettingsProvider><Probe /><SystemSettings /></SystemSettingsProvider>)
    await waitFor(() => expect(api.isLoading).toBe(false))
  }

  it('defaults to the values the generated config always used', () => {
    expect(DEFAULT_SYSTEM_SETTINGS.retryInterval).toBe(1)
    expect(DEFAULT_SYSTEM_SETTINGS.maxCheckAttempts).toBe(3)
  })

  it('shows both controls with the saved values and explains the trade-off', async () => {
    server.retryInterval = 2
    server.maxCheckAttempts = 4
    await renderControls()
    expect(selectFor('Retry interval').value).toBe('2')
    expect(selectFor('Maximum check attempts').value).toBe('4')
    expect(screen.getByText(/slower alerts and fewer false alarms/i)).toBeInTheDocument()
  })

  it('saves both values as system settings', async () => {
    await renderControls()
    fireEvent.change(selectFor('Maximum check attempts'), { target: { value: '5' } })
    fireEvent.change(selectFor('Retry interval'), { target: { value: '2' } })
    await save()
    expect(systemPuts[0].maxCheckAttempts).toBe(5)
    expect(systemPuts[0].retryInterval).toBe(2)
    expect(server.maxCheckAttempts).toBe(5)
  })

  it('only offers retry intervals that fit inside the check interval', async () => {
    server.checkInterval = 2
    await renderControls()
    const values = Array.from(selectFor('Retry interval').options).map((option) => option.value)
    expect(values).toEqual(['1', '2'])
  })

  it('lowers the retry interval when the check interval drops below it', async () => {
    server.checkInterval = 10
    server.retryInterval = 5
    await renderControls()
    fireEvent.change(selectFor('Check interval'), { target: { value: '2' } })
    expect(api.settings.checkInterval).toBe(2)
    expect(api.settings.retryInterval).toBe(2)
    await save()
    expect(systemPuts[0].retryInterval).toBe(2)
  })

  it('shows the server message when the Nagios config is rejected', async () => {
    await renderControls()
    applyError = 'Check settings could not be applied: Nagios reload failed'
    fireEvent.change(selectFor('Maximum check attempts'), { target: { value: '6' } })
    await save()
    expect(screen.getByTestId('error')).toHaveTextContent('Nagios reload failed')
  })
})


describe('Flap detection card', () => {
  beforeEach(() => {
    localStorage.clear()
    server = { ...DEFAULT_SYSTEM_SETTINGS, version: 1 }
    systemPuts = []
    applyError = null
    fetchMock.mockClear()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  async function renderCard() {
    render(<SystemSettingsProvider><Probe /><SystemSettings /></SystemSettingsProvider>)
    await waitFor(() => expect(api.isLoading).toBe(false))
  }

  const toggle = () => screen.getByRole('switch', { name: /flap detection/i })
  const lowInput = () => screen.getByLabelText('Low flap threshold') as HTMLInputElement
  const highInput = () => screen.getByLabelText('High flap threshold') as HTMLInputElement
  // The card and the main settings card each have a Save Changes button.
  const saveButtons = () => screen.getAllByRole('button', { name: /save changes/i })

  it('defaults to detection on with Nagios thresholds', () => {
    expect(DEFAULT_SYSTEM_SETTINGS.flapDetectionEnabled).toBe(true)
    expect(DEFAULT_SYSTEM_SETTINGS.flapLowThreshold).toBeNull()
    expect(DEFAULT_SYSTEM_SETTINGS.flapHighThreshold).toBeNull()
  })

  it('shows the saved values and explains the empty default', async () => {
    server.flapLowThreshold = 10
    server.flapHighThreshold = 30.5
    await renderCard()
    expect(toggle()).toHaveAttribute('aria-checked', 'true')
    expect(lowInput().value).toBe('10')
    expect(highInput().value).toBe('30.5')
    expect(screen.getAllByText(/leave empty to use Nagios's own value/i)).toHaveLength(2)
    expect(screen.getByText(/5% by default/)).toBeInTheDocument()
    expect(screen.getByText(/20% by default/)).toBeInTheDocument()
  })

  it('saves thresholds as system settings', async () => {
    await renderCard()
    fireEvent.change(lowInput(), { target: { value: '10' } })
    fireEvent.change(highInput(), { target: { value: '35' } })
    await save()
    expect(systemPuts[0].flapLowThreshold).toBe(10)
    expect(systemPuts[0].flapHighThreshold).toBe(35)
    expect(server.flapHighThreshold).toBe(35)
  })

  it('clearing a threshold goes back to the Nagios default', async () => {
    server.flapLowThreshold = 10
    await renderCard()
    fireEvent.change(lowInput(), { target: { value: '' } })
    await save()
    expect(systemPuts[0].flapLowThreshold).toBeNull()
  })

  it('turns detection off and disables the threshold inputs', async () => {
    await renderCard()
    fireEvent.click(toggle())
    expect(toggle()).toHaveAttribute('aria-checked', 'false')
    expect(lowInput()).toBeDisabled()
    expect(highInput()).toBeDisabled()
    await save()
    expect(systemPuts[0].flapDetectionEnabled).toBe(false)
  })

  it.each([
    ['101', '', /from 0 to 100/i],
    ['-1', '', /from 0 to 100/i],
    ['abc', '', /from 0 to 100/i],
    ['30', '30', /lower than the high/i],
    ['40', '10', /lower than the high/i],
  ])('blocks low %s / high %s with a message and does not save', async (low, high, message) => {
    await renderCard()
    fireEvent.change(lowInput(), { target: { value: low } })
    fireEvent.change(highInput(), { target: { value: high } })
    expect(screen.getByRole('alert')).toHaveTextContent(message)
    fireEvent.click(saveButtons()[saveButtons().length - 1])
    fireEvent.click(saveButtons()[0])
    await act(async () => {})
    expect(systemPuts).toHaveLength(0)
  })

  it('shows the Nagios message when the config is rejected', async () => {
    await renderCard()
    applyError = 'Check settings could not be applied: Nagios reload failed'
    fireEvent.click(toggle())
    await save()
    expect(screen.getByTestId('error')).toHaveTextContent('Nagios reload failed')
  })
})
