import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiPost } from '../lib/api'
import { exportRows } from '../utils/exportData'

vi.mock('../lib/api', () => ({ apiPost: vi.fn() }))

const meta = { 'Report period': '2024-01-01 to 2024-01-02', 'Reporting time zone': 'UTC', Units: 'Durations are in seconds' }

function capture() {
  const blobs: Blob[] = []
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  URL.createObjectURL = (blob: Blob) => { blobs.push(blob); return 'blob:test' }
  URL.revokeObjectURL = vi.fn()
  return blobs
}

const read = (blob: Blob) => new Promise<string>((resolve) => {
  const reader = new FileReader()
  reader.onload = () => resolve(String(reader.result))
  reader.readAsText(blob)
})

beforeEach(() => { vi.mocked(apiPost).mockResolvedValue({}) })
afterEach(() => vi.restoreAllMocks())

describe('export context metadata and escaping', () => {
  it('writes metadata before the CSV header and keeps the data intact', async () => {
    const blobs = capture()
    exportRows([{ Host: 'web-01', 'Up (seconds)': 80 }], 'CSV', 'host-availability-report', meta)
    const text = await read(blobs[0])
    expect(text.split('\n').slice(0, 4)).toEqual([
      '# Report period: 2024-01-01 to 2024-01-02', '# Reporting time zone: UTC', '# Units: Durations are in seconds', '',
    ])
    expect(text).toContain('Host,Up (seconds)\nweb-01,80')
  })

  it('writes metadata for an empty result and nothing extra without metadata', async () => {
    const blobs = capture()
    exportRows([], 'CSV', 'empty', meta)
    exportRows([{ A: 1 }], 'CSV', 'plain')
    expect(await read(blobs[0])).toContain('# Units: Durations are in seconds')
    expect(await read(blobs[1])).toBe('A\n1')
  })

  it('puts metadata in XLS and escapes cell HTML', async () => {
    const blobs = capture()
    exportRows([{ Output: '<script>alert(1)</script>' }], 'XLS', 'x', meta)
    const html = await read(blobs[0])
    expect(html).toContain('<th>Reporting time zone</th><td>UTC</td>')
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;')
    expect(html).not.toContain('<script>')
  })

  it('puts metadata and escaped cells in the PDF print view', () => {
    const write = vi.fn()
    vi.spyOn(window, 'open').mockReturnValue({ document: { write, close: vi.fn() }, focus: vi.fn(), print: vi.fn() } as unknown as Window)
    exportRows([{ Output: '<b>x</b>' }], 'PDF', 'x', meta)
    const html = String(write.mock.calls[0][0])
    expect(html).toContain('Reporting time zone')
    expect(html).toContain('&lt;b&gt;x&lt;/b&gt;')
  })
})
