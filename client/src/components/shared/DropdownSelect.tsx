import { useEffect, useRef, useState } from 'react'
import { ChevronDown } from 'lucide-react'

export type DropdownOption<T extends string | number> = { value: T; label: string }

type DropdownSelectProps<T extends string | number> = {
  // Names the control for screen readers, like the "Time range" button of TimeRangeSelect.
  label: string
  value: T | null
  options: DropdownOption<T>[]
  onChange: (value: T) => void
  disabled?: boolean
  // Fill the width of a form field (Settings) instead of sizing to the choice (toolbars).
  block?: boolean
}

// The button-and-popover dropdown used across Network Health and the Dashboard (see TimeRangeSelect):
// a rounded button showing the current choice and a chevron, and a card-style list under it with the
// chosen item in the amber highlight. Closes on a choice, on a click elsewhere and on Escape.
export function DropdownSelect<T extends string | number>({ label, value, options, onChange, disabled, block }: DropdownSelectProps<T>) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const current = options.find((option) => option.value === value)

  useEffect(() => {
    if (!open) return
    const close = (event: MouseEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false)
    }
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', escape)
    }
  }, [open])

  return (
    <div className="relative" ref={root}>
      <button
        type="button"
        aria-label={label}
        aria-haspopup="listbox"
        aria-expanded={open}
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        className={`flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[var(--card-alt)] px-3 py-2 text-sm text-[var(--text)] hover:bg-[var(--hover)] disabled:cursor-not-allowed disabled:opacity-50 ${
          block ? 'h-10 w-full justify-between bg-[var(--input-bg)]' : 'max-w-[14rem]'
        }`}
      >
        <span className="truncate">{current?.label ?? '—'}</span>
        <ChevronDown className="h-3.5 w-3.5 shrink-0" />
      </button>
      {open && (
        <div
          role="listbox"
          aria-label={label}
          className={`absolute top-full z-10 mt-2 max-h-64 overflow-y-auto rounded-xl border border-[var(--border)] bg-[var(--card)] p-1.5 shadow-lg ${
            block ? 'left-0 right-0' : 'right-0 min-w-40 max-w-xs'
          }`}
        >
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              role="option"
              aria-selected={option.value === value}
              onClick={() => {
                onChange(option.value)
                setOpen(false)
              }}
              className={`block w-full truncate rounded-lg px-2.5 py-1.5 text-left text-sm ${
                option.value === value ? 'bg-[#F4A90B]/15 text-[#F4A90B]' : 'text-[var(--text)] hover:bg-[var(--hover)]'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
