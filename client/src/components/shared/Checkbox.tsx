import type { InputHTMLAttributes } from 'react'

// The checkbox used in Settings forms: brand-orange when ticked, with the same text size as the
// other field labels (text-sm). Pass the label as children.
export function Checkbox({ children, className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className={`inline-flex cursor-pointer items-center gap-2 text-sm text-[var(--text)] ${className}`}>
      <input
        type="checkbox"
        className="h-4 w-4 shrink-0 cursor-pointer rounded border-[var(--border)] accent-[#ffb100] focus:outline-none focus:ring-2 focus:ring-[#ffb100]/40"
        {...props}
      />
      {children}
    </label>
  )
}
