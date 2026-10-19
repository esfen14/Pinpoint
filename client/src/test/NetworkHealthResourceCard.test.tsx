import { fireEvent, render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ResourceUsageCard } from '../components/network-health/ResourceUsageCard'

// The card used to show a "more options" button that opened nothing; a control that looks clickable but is not misleads users.
describe('ResourceUsageCard header', () => {
  it('shows no "More options" button and keeps the card clickable', () => {
    const onClick = vi.fn()
    render(<ResourceUsageCard cpuPct={20} memoryPct={40} diskPct={60} onClick={onClick} />)
    expect(screen.getByText('Average Resource')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'More options' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('Average Resource'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('shows the three averages', () => {
    render(<ResourceUsageCard cpuPct={20} memoryPct={40} diskPct={null} />)
    expect(screen.getByText('20%')).toBeInTheDocument()
    expect(screen.getByText('40%')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
