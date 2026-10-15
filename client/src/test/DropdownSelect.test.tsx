import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DropdownSelect } from '../components/shared/DropdownSelect'

const OPTIONS = [{ value: 'a', label: 'Alpha' }, { value: 'b', label: 'Beta' }]

describe('DropdownSelect', () => {
  it('shows the current choice and opens a list with it highlighted as selected', () => {
    render(<DropdownSelect label="Pick" value="b" options={OPTIONS} onChange={() => {}} />)

    expect(screen.getByRole('button', { name: 'Pick' })).toHaveTextContent('Beta')
    fireEvent.click(screen.getByRole('button', { name: 'Pick' }))
    expect(screen.getByRole('option', { name: 'Beta' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('option', { name: 'Alpha' })).toHaveAttribute('aria-selected', 'false')
  })

  it('reports a choice and closes', () => {
    const onChange = vi.fn()
    render(<DropdownSelect label="Pick" value="a" options={OPTIONS} onChange={onChange} />)

    fireEvent.click(screen.getByRole('button', { name: 'Pick' }))
    fireEvent.click(screen.getByRole('option', { name: 'Beta' }))

    expect(onChange).toHaveBeenCalledWith('b')
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('closes on Escape and on a click elsewhere', () => {
    render(<div><DropdownSelect label="Pick" value="a" options={OPTIONS} onChange={() => {}} /><p>elsewhere</p></div>)

    fireEvent.click(screen.getByRole('button', { name: 'Pick' }))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Pick' }))
    fireEvent.mouseDown(screen.getByText('elsewhere'))
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('cannot be opened when disabled, and shows a dash for no choice', () => {
    render(<DropdownSelect label="Pick" value={null} options={[]} onChange={() => {}} disabled />)

    expect(screen.getByRole('button', { name: 'Pick' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Pick' })).toHaveTextContent('—')
  })
})
