import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { EmailSettings } from '../components/settings/EmailSettings'
import { ApiError } from '../lib/api'

const get = vi.fn(), save = vi.fn(), send = vi.fn()
vi.mock('../lib/smtpSettingsApi', () => ({
  getSmtpSettings: () => get(), saveSmtpSettings: (...args: unknown[]) => save(...args), sendTestEmail: () => send(),
}))
const gmail = { provider: 'gmail', host: 'smtp.gmail.com', port: 587, tls: 'starttls' }
const custom = { provider: 'custom', host: '', port: 587, tls: 'starttls' }
const settings = { ...gmail, username: 'ops@example.org', sender: 'ops@example.org', passwordSet: true, configured: true, version: 3, updatedAt: null }
const failure = { time: '2026-10-15T01:02:03+00:00', reason: 'Notification mail transport is not configured.' }
const loaded = (lastMailFailure: typeof failure | null = null) => ({ settings, presets: { gmail, custom }, lastMailFailure })

beforeEach(() => {
  get.mockReset().mockResolvedValue(loaded())
  save.mockReset().mockResolvedValue({ ...settings, ...custom, host: 'mail.example.org', port: 2525, username: 'monitoring', version: 4 })
  send.mockReset()
})

function chooseRelay() {
  fireEvent.change(screen.getByRole('combobox'), { target: { value: 'custom' } })
}

describe('custom relay', () => {
  it('shows editable relay fields, saves and clears only the entered password', async () => {
    render(<EmailSettings />)
    await screen.findByLabelText('Host'); chooseRelay()
    expect(screen.getByLabelText('Host')).toBeEnabled()
    fireEvent.change(screen.getByLabelText('Host'), { target: { value: 'mail.example.org' } })
    fireEvent.change(screen.getByLabelText('Port'), { target: { value: '2525' } })
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'monitoring' } })
    fireEvent.change(screen.getByLabelText('Sender'), { target: { value: 'alerts@example.org' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'temporary-token' } })
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password')
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/ }))
    await waitFor(() => expect(save).toHaveBeenCalledWith({ provider: 'custom', host: 'mail.example.org', port: 2525, tls: 'starttls', username: 'monitoring', sender: 'alerts@example.org', password: 'temporary-token' }, 3))
    await waitFor(() => expect(screen.getByLabelText('Password')).toHaveValue(''))
    expect(JSON.stringify(localStorage)).not.toContain('temporary-token')
    expect(JSON.stringify(sessionStorage)).not.toContain('temporary-token')
  })

  it.each([['Host', 'bad host', /host/i], ['Port', '65536', /port/i], ['Port', '1.5', /port/i]])('validates %s before saving', async (label, value, message) => {
    render(<EmailSettings />)
    await screen.findByLabelText('Host'); chooseRelay()
    fireEvent.change(screen.getByLabelText('Host'), { target: { value: 'mail.example.org' } })
    fireEvent.change(screen.getByLabelText(label), { target: { value } })
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/ }))
    expect(await screen.findByText(message, { selector: 'span.text-red-500' })).toBeInTheDocument()
    expect(save).not.toHaveBeenCalled()
  })

  it('keeps the saved password when blank and shows server errors', async () => {
    save.mockRejectedValue(new ApiError('The sender was refused by the relay.', 400))
    render(<EmailSettings />)
    await screen.findByLabelText('Host'); chooseRelay()
    fireEvent.change(screen.getByLabelText('Host'), { target: { value: 'mail.example.org' } })
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/ }))
    expect(await screen.findByText('The sender was refused by the relay.')).toBeInTheDocument()
    expect(save.mock.calls[0][0]).not.toHaveProperty('password')
  })

  it('discards provider changes and restores Gmail help', async () => {
    render(<EmailSettings />)
    await screen.findByLabelText('Host'); chooseRelay()
    expect(screen.queryByText(/Gmail does not accept your normal password here/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Discard Changes/ }))
    expect(screen.getByLabelText('Host')).toHaveValue('smtp.gmail.com')
    expect(screen.getByLabelText('Host')).toBeDisabled()
    expect(screen.getByLabelText('App password')).toHaveValue('')
  })
})

describe('mail failure notice', () => {
  it('shows time, safe reason and a link to test settings', async () => {
    get.mockResolvedValue(loaded(failure))
    render(<EmailSettings />)
    expect(await screen.findByText(failure.reason)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Test email settings/ })).toHaveAttribute('href', '#smtp-test-email')
    expect(screen.getByText(/15\/10\/2026/)).toBeInTheDocument()
  })

  it('refreshes the indicator and clears it without replacing unsaved edits', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      get.mockResolvedValueOnce(loaded(failure)).mockResolvedValue(loaded())
      render(<EmailSettings />)
      await screen.findByText(failure.reason)
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'unsaved@example.org' } })
      await act(async () => { await vi.advanceTimersByTimeAsync(30000) })
      expect(get).toHaveBeenCalledTimes(2)
      expect(screen.queryByText(failure.reason)).not.toBeInTheDocument()
      expect(screen.getByLabelText('Username')).toHaveValue('unsaved@example.org')
    } finally { vi.useRealTimers() }
  })
})
