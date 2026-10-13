import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { Pagination, pageItems } from '../components/shared/Pagination'

describe('pageItems', () => {
  it('lists every page when there are up to four', () => {
    expect(pageItems(1, 1)).toEqual([1])
    expect(pageItems(1, 2)).toEqual([1, 2])
    expect(pageItems(2, 3)).toEqual([1, 2, 3])
    expect(pageItems(4, 4)).toEqual([1, 2, 3, 4])
  })

  it('shows 1 2 3 … last from the start', () => {
    expect(pageItems(1, 9)).toEqual([1, 2, 3, 'gap', 9])
    expect(pageItems(3, 9)).toEqual([1, 2, 3, 'gap', 9])
  })

  it('slides through the middle and the end', () => {
    expect(pageItems(5, 9)).toEqual([1, 'gap', 4, 5, 6, 'gap', 9])
    expect(pageItems(8, 9)).toEqual([1, 'gap', 7, 8, 9])
  })
})

describe('Pagination', () => {
  it('marks the current page and changes page on click', () => {
    const onPageChange = vi.fn()
    render(<Pagination page={2} pageCount={9} onPageChange={onPageChange} />)

    expect(screen.getByText('2')).toHaveAttribute('aria-current', 'page')
    fireEvent.click(screen.getByRole('button', { name: 'Page 3' }))
    expect(onPageChange).toHaveBeenCalledWith(3)
    fireEvent.click(screen.getByRole('button', { name: 'Page 9' }))
    expect(onPageChange).toHaveBeenCalledWith(9)
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(onPageChange).toHaveBeenCalledWith(3)
  })

  it('disables Previous on the first page and Next on the last', () => {
    const { rerender } = render(<Pagination page={1} pageCount={2} onPageChange={() => {}} />)
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
    rerender(<Pagination page={2} pageCount={2} onPageChange={() => {}} />)
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
  })
})
