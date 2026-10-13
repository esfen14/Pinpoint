import { Fragment } from 'react'

type Props = {
  page: number
  pageCount: number
  onPageChange: (page: number) => void
  // 'themed' follows the CSS variables used by the Accounts, Logs and History pages.
  variant?: 'default' | 'themed'
  disabled?: boolean
}

// Page numbers to show: every page up to four, otherwise the first three then "…" then the
// last (1 2 3 … 9), sliding to 1 … 4 5 6 … 9 in the middle and 1 … 7 8 9 at the end.
// eslint-disable-next-line react-refresh/only-export-components
export function pageItems(page: number, pageCount: number): (number | 'gap')[] {
  if (pageCount <= 4) return Array.from({ length: pageCount }, (_, i) => i + 1)
  if (page <= 3) return [1, 2, 3, 'gap', pageCount]
  if (page >= pageCount - 2) return [1, 'gap', pageCount - 2, pageCount - 1, pageCount]
  return [1, 'gap', page - 1, page, page + 1, 'gap', pageCount]
}

export function Pagination({ page, pageCount, onPageChange, variant = 'default', disabled = false }: Props) {
  const hover = variant === 'themed' ? 'hover:bg-[var(--hover)]' : 'hover:bg-gray-100 dark:hover:bg-white/10'
  const base = `rounded-lg px-3 py-1 ${hover} disabled:cursor-not-allowed disabled:opacity-50`
  const current =
    'rounded-lg border border-gray-200 bg-white px-3 py-1 text-gray-900 shadow-sm dark:border-transparent dark:bg-white/10 dark:text-white'
  const items = pageItems(page, pageCount)

  return (
    <nav aria-label="Pagination" className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={disabled || page <= 1}
        className={base}
      >
        Previous
      </button>

      {items.map((item, index) =>
        item === 'gap' ? (
          <span key={`gap-${index}`} aria-hidden="true" className="px-1 text-gray-400">
            …
          </span>
        ) : (
          <Fragment key={item}>
            {item === page ? (
              <span aria-current="page" className={current}>
                {item}
              </span>
            ) : (
              <button
                type="button"
                onClick={() => onPageChange(item)}
                disabled={disabled}
                aria-label={`Page ${item}`}
                className={base}
              >
                {item}
              </button>
            )}
          </Fragment>
        ),
      )}

      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={disabled || page >= pageCount}
        className={base}
      >
        Next
      </button>
    </nav>
  )
}
