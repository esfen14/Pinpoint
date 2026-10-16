import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../lib/api'
import { NotificationPolicySettings } from '../components/settings/NotificationPolicySettings'

const getPolicy = vi.fn()
const savePolicy = vi.fn()
vi.mock('../lib/notificationPolicyApi', () => ({
  getNotificationPolicy: () => getPolicy(),
  saveNotificationPolicy: (...args: unknown[]) => savePolicy(...args),
}))
const initial = { quietHours: [], hostOptions: ['d', 'u', 'r', 'f', 's'], serviceOptions: ['w', 'u', 'c', 'r', 'f', 's'], renotifyInterval: 30, version: 1, timeZone: 'Nagios server local time' }

describe('NotificationPolicySettings', () => {
  beforeEach(() => { getPolicy.mockReset().mockResolvedValue(structuredClone(initial)); savePolicy.mockReset() })
  it('edits, saves, removes and reloads quiet hours and options', async () => {
    savePolicy.mockImplementation(async (data) => ({ ...data, version: 2 }))
    render(<NotificationPolicySettings />)
    expect(await screen.findByText(/No quiet hours/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Add quiet hours' }))
    fireEvent.change(screen.getByLabelText('Start 1'), { target: { value: '09:00' } })
    fireEvent.change(screen.getByLabelText('End 1'), { target: { value: '10:00' } })
    fireEvent.click(screen.getByRole('switch', { name: 'Down' }))
    fireEvent.change(screen.getByLabelText('Renotify interval (minutes)'), { target: { value: '15' } })
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }))
    await waitFor(() => expect(savePolicy).toHaveBeenCalledWith(expect.objectContaining({ renotifyInterval: 15, hostOptions: ['u', 'r', 'f', 's'], quietHours: [{ weekday: 'monday', start: '09:00', end: '10:00' }] })))
    expect(await screen.findByText('Policy saved.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Remove quiet hours 1' }))
    expect(screen.getByText(/No quiet hours/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Reload policy/i }))
    await waitFor(() => expect(getPolicy).toHaveBeenCalledTimes(2))
  })
  it('blocks invalid times, overlap and interval before requesting a save', async () => {
    render(<NotificationPolicySettings />)
    await screen.findByText(/No quiet hours/i)
    fireEvent.click(screen.getByRole('button', { name: 'Add quiet hours' }))
    fireEvent.change(screen.getByLabelText('Start 1'), { target: { value: '22:00' } })
    fireEvent.change(screen.getByLabelText('End 1'), { target: { value: '07:00' } })
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/start.*before end/i)
    expect(savePolicy).not.toHaveBeenCalled()
    fireEvent.change(screen.getByLabelText('Start 1'), { target: { value: '09:00' } })
    fireEvent.change(screen.getByLabelText('End 1'), { target: { value: '11:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add quiet hours' }))
    fireEvent.change(screen.getByLabelText('Start 2'), { target: { value: '10:00' } })
    fireEvent.change(screen.getByLabelText('End 2'), { target: { value: '12:00' } })
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/overlap/i)
    fireEvent.click(screen.getByRole('button', { name: 'Remove quiet hours 2' }))
    fireEvent.change(screen.getByLabelText('Renotify interval (minutes)'), { target: { value: '1441' } })
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/renotify interval/i)
    expect(savePolicy).not.toHaveBeenCalled()
  })
  it.each([[400, 'Bad quietHours'], [409, 'Someone else saved'], [422, 'Nagios rejected policy']])('shows %s server message', async (status, message) => {
    savePolicy.mockRejectedValue(new ApiError(message, status))
    render(<NotificationPolicySettings />)
    await screen.findByText(/No quiet hours/i)
    fireEvent.change(screen.getByLabelText('Renotify interval (minutes)'), { target: { value: '12' } })
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    if (status === 409) expect(within(screen.getByRole('alert')).getByRole('button', { name: /Reload/i })).toBeInTheDocument()
  })
})
