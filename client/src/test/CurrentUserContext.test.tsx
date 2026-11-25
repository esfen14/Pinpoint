import { act, render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { CurrentUserProvider, useCurrentUser } from '../contexts/CurrentUserContext'
import { UNAUTHORIZED_EVENT } from '../lib/api'

const fetchMock = vi.fn()

let me: Record<string, unknown>
let status: number
const onRender = vi.fn()

function Probe() {
  const { user } = useCurrentUser()
  onRender()
  return <div>{user ? `Signed in as ${user.firstName}` : 'No user'}</div>
}

async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms)
  })
}

async function renderProvider() {
  render(
    <CurrentUserProvider>
      <Probe />
    </CurrentUserProvider>,
  )
  await advance(0)
}

describe('CurrentUserProvider session check', () => {
  const unauthorized = vi.fn()

  beforeEach(() => {
    vi.useFakeTimers()
    onRender.mockReset()
    status = 200
    me = { first_name: 'Emily', permissions: [] }
    unauthorized.mockReset()
    window.addEventListener(UNAUTHORIZED_EVENT, unauthorized)
    fetchMock.mockReset()
    fetchMock.mockImplementation(() =>
      Promise.resolve({
        ok: status < 400,
        status,
        json: () => Promise.resolve({ data: me }),
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    window.removeEventListener(UNAUTHORIZED_EVENT, unauthorized)
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('checks the session every 10 seconds', async () => {
    await renderProvider()

    await advance(30_000)

    expect(fetchMock).toHaveBeenCalledTimes(4)
  })

  it('reports a session that ended while the page was idle', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    await renderProvider()

    status = 401
    await advance(10_000)

    expect(unauthorized).toHaveBeenCalled()
  })

  it('shows a name change without a refresh', async () => {
    await renderProvider()

    me = { first_name: 'Emma', permissions: [] }
    await advance(10_000)

    expect(screen.getByText('Signed in as Emma')).toBeInTheDocument()
  })

  it('does not re-render the app when nothing changed', async () => {
    await renderProvider()
    onRender.mockClear()

    await advance(30_000)

    expect(onRender).not.toHaveBeenCalled()
  })

  it('does not check while the tab is hidden', async () => {
    await renderProvider()
    vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('hidden')

    await advance(30_000)

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  // Setup and password change replace the session's sign-in details; a check
  // sent while that request is running would still carry the old session.
  it.each([
    ['needs_setup'],
    ['must_change_password'],
  ])('does not check while the account is flagged %s', async (flag) => {
    me = { first_name: 'Emily', permissions: [], [flag]: true }
    await renderProvider()

    await advance(30_000)

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
