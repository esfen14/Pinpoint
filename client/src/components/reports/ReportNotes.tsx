import type { ReactNode } from 'react'

// The explanatory text for a report, kept out of the way below its table.
export function ReportNotes({ description, children }: { description: string; children?: ReactNode }) {
  return (
    <section aria-label="About this report" className="space-y-2 px-1 text-[13px] leading-relaxed text-gray-500 dark:text-gray-400">
      <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300">About this report</h2>
      <p>{description}</p>
      {children}
    </section>
  )
}
