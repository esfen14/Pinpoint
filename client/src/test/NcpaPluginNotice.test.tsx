import { act, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NcpaDeploymentPage } from '../pages/NcpaDeploymentPage'
import { useNcpaPluginState } from '../hooks/useNcpaPluginState'
import type { PluginListItem } from '../types/plugin'

const plugins = vi.hoisted(() => ({ getPluginInventory: vi.fn() }))
vi.mock('../lib/pluginApi', () => plugins)

const ncpa = vi.hoisted(() => ({
  getNcpaDevices: vi.fn(),
  getRuns: vi.fn(),
  getRun: vi.fn(),
  reviewRun: vi.fn(),
  getLatestRun: vi.fn(),
  stopDeployment: vi.fn(),
  getLiveFingerprint: vi.fn(),
  confirmTrust: vi.fn(),
  checkCredentials: vi.fn(),
  startDeployment: vi.fn(),
}))
vi.mock('../lib/ncpaDeploymentApi', () => ({ ...ncpa, NCPA_DEPLOYMENT_STARTED_EVENT: 'nds:ncpa-deployment-started' }))

vi.mock('../contexts/SystemSettingsContext', () => ({
  useSystemSettings: () => ({ settings: { dateTimeFormat: 'DD/MM/YYYY', timeZone: 'UTC+00:00' } }),
}))

function plugin(overrides: Partial<PluginListItem> = {}): PluginListItem {
  return {
    id: 9, name: 'check_ncpa', display_name: null, description: null, category: null, type: 'Nagios',
    source: 'Baseline (ISO)', status: 'Ready', current_version: null, updated_at: '2026-10-05T00:00:00Z',
    service_driven: true, monitoring_usage: { services: 0, devices: 0 }, ...overrides,
  }
}

const inventory = (items: PluginListItem[]) =>
  Promise.resolve({ items, page: 1, per_page: 10, pages: 1, total: items.length, has_next: false, has_prev: false })

describe('useNcpaPluginState', () => {
  afterEach(() => vi.restoreAllMocks())
  beforeEach(() => {
    plugins.getPluginInventory.mockReset()
  })

  it.each([
    ['Enabled', 'enabled'], ['Active', 'enabled'],
    ['Ready', 'not-enabled'], ['Disabled', 'not-enabled'], ['Installed', 'not-enabled'],
  ])('maps a %s check_ncpa to %s', async (status, expected) => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: status as PluginListItem['status'] })]))
    const { result } = renderHook(() => useNcpaPluginState())

    await waitFor(() => expect(result.current).toBe(expected))
    expect(plugins.getPluginInventory).toHaveBeenCalledWith({ search: 'check_ncpa', per_page: 10, sort_by: 'name', order: 'asc' })
  })

  it.each(['check_ncpa.py', 'check_ncpa.pl', 'check_ncpa.sh', ' CHECK_NCPA.PY '])(
    'recognizes enabled script inventory name %s', async (name) => {
      plugins.getPluginInventory.mockReturnValue(inventory([plugin({ name, status: 'Enabled' })]))
      const { result } = renderHook(() => useNcpaPluginState())
      await waitFor(() => expect(result.current).toBe('enabled'))
    },
  )

  it('uses any enabled canonical duplicate, rather than the first disabled filename', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([
      plugin({ status: 'Disabled' }), plugin({ name: 'check_ncpa.py', status: 'Active' }),
    ]))
    const { result } = renderHook(() => useNcpaPluginState())
    await waitFor(() => expect(result.current).toBe('enabled'))
  })

  it('rejects lookalike script filenames', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ name: 'check_ncpa.py.bak', status: 'Active' })]))
    const { result } = renderHook(() => useNcpaPluginState())
    await waitFor(() => expect(result.current).toBe('not-enabled'))
  })

  it('refreshes a disabled plugin after the open window gains focus', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Disabled' })]))
    const { result } = renderHook(() => useNcpaPluginState())
    await waitFor(() => expect(result.current).toBe('not-enabled'))
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Enabled' })]))
    fireEvent.focus(window)
    await waitFor(() => expect(result.current).toBe('enabled'))
  })

  it('refreshes when the document becomes visible, including a disable transition', async () => {
    const visibility = vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('visible')
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Active' })]))
    const { result } = renderHook(() => useNcpaPluginState())
    await waitFor(() => expect(result.current).toBe('enabled'))
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Disabled' })]))
    visibility.mockReturnValue('hidden')
    fireEvent(document, new Event('visibilitychange'))
    expect(plugins.getPluginInventory).toHaveBeenCalledTimes(1)
    visibility.mockReturnValue('visible')
    fireEvent(document, new Event('visibilitychange'))
    await waitFor(() => expect(result.current).toBe('not-enabled'))
  })

  it('clears a stale warning to unknown when refresh fails or permission is denied', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Disabled' })]))
    const { result } = renderHook(() => useNcpaPluginState())
    await waitFor(() => expect(result.current).toBe('not-enabled'))
    plugins.getPluginInventory.mockRejectedValue(new Error('403'))
    fireEvent.focus(window)
    await waitFor(() => expect(result.current).toBe('unknown'))
  })

  it('ignores an older response after a newer refresh has completed', async () => {
    let finishOld!: (value: Awaited<ReturnType<typeof inventory>>) => void
    plugins.getPluginInventory.mockReturnValue(new Promise((resolve) => { finishOld = resolve }))
    const { result } = renderHook(() => useNcpaPluginState())
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Active' })]))
    fireEvent.focus(window)
    await waitFor(() => expect(result.current).toBe('enabled'))
    await act(async () => { finishOld(await inventory([plugin({ status: 'Disabled' })])) })
    expect(result.current).toBe('enabled')
  })

  it('removes listeners when unmounted', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Enabled' })]))
    const { result, unmount } = renderHook(() => useNcpaPluginState())
    await waitFor(() => expect(result.current).toBe('enabled'))
    unmount()
    fireEvent.focus(window)
    fireEvent(document, new Event('visibilitychange'))
    expect(plugins.getPluginInventory).toHaveBeenCalledTimes(1)
  })

  it('treats a missing check_ncpa as not enabled', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ name: 'check_ncpa_extra', status: 'Active' })]))
    const { result } = renderHook(() => useNcpaPluginState())

    await waitFor(() => expect(result.current).toBe('not-enabled'))
  })

  it('stays unknown when the inventory cannot be read', async () => {
    plugins.getPluginInventory.mockRejectedValue(new Error('403'))
    const { result } = renderHook(() => useNcpaPluginState())

    await waitFor(() => expect(plugins.getPluginInventory).toHaveBeenCalled())
    expect(result.current).toBe('unknown')
  })
})

describe('NcpaDeploymentPage plugin notice', () => {
  beforeEach(() => {
    Object.values(ncpa).forEach((fn) => fn.mockReset())
    ncpa.getNcpaDevices.mockResolvedValue([])
    ncpa.getLatestRun.mockResolvedValue(null)
    ncpa.getRuns.mockResolvedValue({ items: [], page: 1, pages: 1, total: 0, hasNext: false, hasPrev: false, needsReview: 0 })
    plugins.getPluginInventory.mockReset()
  })

  const renderPage = () =>
    render(
      <MemoryRouter initialEntries={['/ncpa-deployment']}>
        <Routes>
          <Route path="/ncpa-deployment" element={<NcpaDeploymentPage />} />
          <Route path="/plugins" element={<Link to="/ncpa-deployment">Return to deployment</Link>} />
        </Routes>
      </MemoryRouter>,
    )

  it('warns that NCPA checks are not monitored while check_ncpa is off, and links to Plugin Manager', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Ready' })]))
    renderPage()

    expect(await screen.findByText(/check_ncpa plugin is not enabled in Plugin Manager/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'enable check_ncpa' })).toHaveAttribute('href', '/plugins')
  })

  it('shows no warning once check_ncpa is enabled', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Active' })]))
    renderPage()

    await waitFor(() => expect(plugins.getPluginInventory).toHaveBeenCalled())
    await screen.findByText('NCPA Deployment')
    expect(screen.queryByText(/is not enabled in Plugin Manager/)).not.toBeInTheDocument()
  })

  it('fetches current inventory when returning from Plugin Manager', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Disabled' })]))
    renderPage()
    fireEvent.click(await screen.findByRole('link', { name: 'enable check_ncpa' }))
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Enabled' })]))
    fireEvent.click(screen.getByRole('link', { name: 'Return to deployment' }))
    await waitFor(() => expect(plugins.getPluginInventory).toHaveBeenCalledTimes(2))
    expect(screen.queryByText(/is not enabled in Plugin Manager/)).not.toBeInTheDocument()
  })

  it('shows no warning when the plugin state cannot be read', async () => {
    plugins.getPluginInventory.mockRejectedValue(new Error('403'))
    renderPage()

    await screen.findByText('NCPA Deployment')
    await waitFor(() => expect(plugins.getPluginInventory).toHaveBeenCalled())
    expect(screen.queryByText(/is not enabled in Plugin Manager/)).not.toBeInTheDocument()
  })
})


describe('NCPA warning after plugin transitions', () => {
  beforeEach(() => {
    Object.values(ncpa).forEach((fn) => fn.mockReset())
    ncpa.getNcpaDevices.mockResolvedValue([])
    ncpa.getLatestRun.mockResolvedValue(null)
    ncpa.getRuns.mockResolvedValue({ items: [], page: 1, pages: 1, total: 0, hasNext: false, hasPrev: false, needsReview: 0 })
    plugins.getPluginInventory.mockReset()
  })

  it('clears and restores the rendered banner on focus after enable and disable', async () => {
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Disabled' })]))
    render(<MemoryRouter><NcpaDeploymentPage /></MemoryRouter>)
    await screen.findByText(/check_ncpa plugin is not enabled/)
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Active' })]))
    fireEvent.focus(window)
    await waitFor(() => expect(screen.queryByText(/check_ncpa plugin is not enabled/)).not.toBeInTheDocument())
    plugins.getPluginInventory.mockReturnValue(inventory([plugin({ status: 'Disabled' })]))
    fireEvent.focus(window)
    await screen.findByText(/check_ncpa plugin is not enabled/)
  })
})
