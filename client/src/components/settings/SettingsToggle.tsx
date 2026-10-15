interface SettingsToggleProps {
  label: string
  description?: string
  /** A small colour dot before the label (for example the colour of a state). */
  dotClass?: string
  enabled: boolean
  onChange: (enabled: boolean) => void
}

export function SettingsToggle({
  label,
  description,
  dotClass,
  enabled,
  onChange,
}: SettingsToggleProps) {
  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-sm font-medium text-[var(--text)]">
            {dotClass && <span aria-hidden="true" className={`h-2 w-2 shrink-0 rounded-full ${dotClass}`} />}
            {label}
          </p>

          {description && (
            <p className="mt-1.5 text-xs text-[var(--text-muted)]">
              {description}
            </p>
          )}
        </div>

        <button
          type="button"
          role="switch"
          aria-label={label}
          aria-checked={enabled}
          onClick={() => onChange(!enabled)}
          className={`
            relative
            h-6
            w-11
            shrink-0
            rounded-full
            border
            transition-colors
            duration-200
            focus:outline-none
            focus:ring-2
            focus:ring-orange-400/40
            ${
              enabled
                ? 'border-orange-500 bg-orange-500'
                : 'border-gray-400 bg-gray-300 dark:border-gray-600 dark:bg-gray-700'
            }
          `}
        >
          <span
            className={`
              absolute
              top-0.5
              h-5
              w-5
              rounded-full
              bg-white
              shadow-md
              transition-all
              duration-200
              ${
                enabled
                  ? 'left-5.5'
                  : 'left-0.5'
              }
            `}
          />
        </button>
      </div>
    </div>
  )
}