import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DrawerShell } from '../components/shared/DrawerShell'

describe('DrawerShell', () => {
  it('shows the title and children, and closes from the close button', () => {
    const onClose = vi.fn()
    render(<DrawerShell title="Run 4" onClose={onClose}><section>Body</section></DrawerShell>)
    expect(screen.getByRole('heading', { name: 'Run 4' })).toBeInTheDocument()
    expect(screen.getByText('Body')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(onClose).toHaveBeenCalled()
  })

  it('offers a back button only when asked', () => {
    const onBack = vi.fn()
    const { rerender } = render(<DrawerShell title="t" onClose={() => {}}>x</DrawerShell>)
    expect(screen.queryByRole('button', { name: 'Back to host' })).not.toBeInTheDocument()
    rerender(<DrawerShell title="t" onClose={() => {}} onBack={onBack} backLabel="Back to host">x</DrawerShell>)
    fireEvent.click(screen.getByRole('button', { name: 'Back to host' }))
    expect(onBack).toHaveBeenCalled()
  })

  it('is a labelled dialog that closes on an outside click when asked', () => {
    const onClose = vi.fn()
    render(<DrawerShell title="Deployment" titleId="t1" dialog dismissOnOverlay onClose={onClose}>x</DrawerShell>)
    const dialog = screen.getByRole('dialog', { name: 'Deployment' })
    fireEvent.mouseDown(dialog)
    expect(onClose).not.toHaveBeenCalled()
    fireEvent.mouseDown(dialog.parentElement as HTMLElement)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not close on an outside click by default, and renders the overlay card', () => {
    const onClose = vi.fn()
    const { container } = render(<DrawerShell title="t" onClose={onClose} overlay={<p>Confirm?</p>}>x</DrawerShell>)
    fireEvent.mouseDown(container.firstChild as HTMLElement)
    expect(onClose).not.toHaveBeenCalled()
    expect(screen.getByText('Confirm?')).toBeInTheDocument()
  })
})
