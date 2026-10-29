import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useNetworkRescan } from '../hooks/useNetworkRescan'

function reply(data: unknown) {
  return { ok: true, status: 200, text: async () => JSON.stringify({ success: true, data }) }
}

describe('useNetworkRescan', () => {
  afterEach(() => vi.unstubAllGlobals())

  it.each([
    ['focused', '10.0.0.4', '{"target":"10.0.0.4"}'],
    ['full', undefined, undefined],
  ])('starts a %s scan with the correct request body', async (_mode, target, body) => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(reply(null))
      .mockResolvedValueOnce(reply(null))
    vi.stubGlobal('fetch', fetchMock)
    const { result, unmount } = renderHook(() => useNetworkRescan())
    await act(async () => { await result.current.start(target) })
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[1][0]).toBe('/api/system/discover/start')
    expect(fetchMock.mock.calls[1][1].body).toBe(body)
    unmount()
  })
})
