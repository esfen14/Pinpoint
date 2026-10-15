import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { EscalationSettings } from '../components/settings/EscalationSettings'
import { ApiError } from '../lib/api'

let permitted = true
const list = vi.fn(), create = vi.fn(), update = vi.fn(), remove = vi.fn()
vi.mock('../contexts/CurrentUserContext', () => ({ useCurrentUser: () => ({ hasPermission: () => permitted }) }))
vi.mock('../lib/escalationApi', () => ({
  getEscalations: () => list(), createEscalation: (...args: unknown[]) => create(...args),
  updateEscalation: (...args: unknown[]) => update(...args), deleteEscalation: (...args: unknown[]) => remove(...args),
}))
const item = { id: 1, contact_group: 'system_users', first_notification: 2, last_notification: 5, interval_minutes: 10, host_id: null, active: true, reason: '' }
const choices = { items: [], groups: [{ name: 'system_users', member_count: 2 }], hosts: [{ id: 4, name: 'web01' }] }
beforeEach(() => {
  permitted = true
  vi.resetAllMocks()
  list.mockResolvedValue(structuredClone(choices))
  create.mockResolvedValue(item)
  update.mockResolvedValue(item)
  remove.mockResolvedValue(null)
})
describe('EscalationSettings', () => {
  it('hides the card without permission and never fetches', () => {
    permitted = false
    render(<EscalationSettings />)
    expect(screen.queryByText('Escalations')).not.toBeInTheDocument()
    expect(list).not.toHaveBeenCalled()
  })
  it('shows loading, retries errors, and explains the empty list', async () => {
    list.mockRejectedValueOnce(new Error('Unavailable'))
    render(<EscalationSettings />)
    expect(screen.getByRole('status')).toHaveTextContent(/loading/i)
    expect(await screen.findByRole('alert')).toHaveTextContent('Unavailable')
    fireEvent.click(screen.getByRole('button', { name: 'Retry escalations' }))
    expect(await screen.findByText('No escalations defined.')).toBeInTheDocument()
  })
  it('adds a scoped range and reloads persisted rows', async () => {
    render(<EscalationSettings />)
    await screen.findByText('No escalations defined.')
    fireEvent.click(screen.getByRole('button', { name: 'Scope' }))
    fireEvent.click(screen.getByRole('option', { name: 'web01' }))
    list.mockResolvedValue({ ...choices, items: [{ ...item, host_id: 4 }] })
    fireEvent.click(screen.getByRole('button', { name: 'Add escalation' }))
    await waitFor(() => expect(create).toHaveBeenCalledWith({ contact_group: 'system_users', first_notification: 2, last_notification: 5, interval_minutes: 10, host_id: 4 }))
    expect(await screen.findByText('Escalation saved.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Reload escalations' }))
    await waitFor(() => expect(list).toHaveBeenCalledTimes(3))
  })
  it('edits and confirms deletion', async () => {
    list.mockResolvedValue({ ...choices, items: [item] })
    render(<EscalationSettings />)
    fireEvent.click(await screen.findByRole('button', { name: 'Edit escalation 1' }))
    fireEvent.change(screen.getByLabelText('Interval (minutes)'), { target: { value: '15' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save escalation' }))
    await waitFor(() => expect(update).toHaveBeenCalledWith(1, { contact_group: 'system_users', first_notification: 2, last_notification: 5, interval_minutes: 15, host_id: null }))
    fireEvent.click(await screen.findByRole('button', { name: 'Delete escalation 1' }))
    expect(screen.getByRole('alertdialog')).toBeInTheDocument()
    expect(remove).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel deletion' }))
    expect(remove).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Delete escalation 1' }))
    list.mockResolvedValue(choices)
    fireEvent.click(screen.getByRole('button', { name: 'Confirm deletion' }))
    await waitFor(() => expect(remove).toHaveBeenCalledWith(1))
    expect(await screen.findByText('Escalation deleted.')).toBeInTheDocument()
  })
  it.each([['First notification', '6', /first notification/i], ['Last notification', '0', /last notification/i], ['Interval (minutes)', '1441', /interval/i], ['Interval (minutes)', '', /interval/i]])('blocks invalid %s', async (label, value, message) => {
    render(<EscalationSettings />)
    await screen.findByText('No escalations defined.')
    fireEvent.change(screen.getByLabelText(label), { target: { value } })
    fireEvent.click(screen.getByRole('button', { name: 'Add escalation' }))
    expect(screen.getByRole('alert')).toHaveTextContent(message)
    expect(create).not.toHaveBeenCalled()
  })
  it.each([400, 422])('displays server %s and retains the draft', async (status) => {
    create.mockRejectedValue(new ApiError('Server rejected range', status))
    render(<EscalationSettings />)
    await screen.findByText('No escalations defined.')
    fireEvent.click(screen.getByRole('button', { name: 'Add escalation' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Server rejected range')
    expect(screen.getByLabelText('First notification')).toHaveValue('2')
  })
  it('disables the form for empty groups but permits deleting inactive rows', async () => {
    list.mockResolvedValue({ ...choices, groups: [{ name: 'system_users', member_count: 0 }], items: [{ ...item, active: false, reason: 'No eligible members.' }] })
    render(<EscalationSettings />)
    expect(await screen.findByText(/No recipient group has eligible members/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add escalation' })).toBeDisabled()
    expect(screen.getByLabelText('First notification')).toBeDisabled()
    expect(screen.getByText('No eligible members.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete escalation 1' })).toBeEnabled()
  })
})
