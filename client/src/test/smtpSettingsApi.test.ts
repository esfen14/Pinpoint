import { afterEach, expect, it, vi } from 'vitest'
import { saveSmtpSettings } from '../lib/smtpSettingsApi'

afterEach(() => vi.unstubAllGlobals())

it('preserves the Gmail request body and passes explicit custom STARTTLS fields', async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, text: async () => JSON.stringify({ success: true, data: {} }) })
  vi.stubGlobal('fetch', fetch)
  await saveSmtpSettings({ username: 'ops@gmail.com', sender: 'ops@gmail.com' }, 3)
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ provider: 'gmail', username: 'ops@gmail.com', sender: 'ops@gmail.com', version: 3 })
  await saveSmtpSettings({ provider: 'custom', host: 'mail.example.org', port: 2525, tls: 'starttls', username: 'monitor', sender: 'ops@example.org' }, 4)
  expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({ provider: 'custom', host: 'mail.example.org', port: 2525, tls: 'starttls', username: 'monitor', sender: 'ops@example.org', version: 4 })
  expect(fetch.mock.calls[1][1]).toMatchObject({ credentials: 'include', method: 'PUT' })
})
