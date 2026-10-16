import type { ReactNode } from 'react'
import { ArrowLeft, X } from 'lucide-react'

type Props = {
  // The heading in the sticky header (a string, or the heading's content).
  title: ReactNode
  // Names the dialog for screen readers when the panel is a dialog (see `dialog`).
  titleId?: string
  ariaLabel?: string
  onClose: () => void
  // Shows a back arrow before the title (a drawer with a second level, like a host and its service).
  onBack?: () => void
  backLabel?: string
  // Marks the panel as a modal dialog.
  dialog?: boolean
  // Closes on a click on the dimmed area outside the panel.
  dismissOnOverlay?: boolean
  // Rendered over the panel inside the dimmed area, e.g. a confirmation card.
  overlay?: ReactNode
  children: ReactNode
}

// The one layout every detail drawer shares (Device Inventory, Plugin Manager, NCPA deployment runs,
// Remediation runs): a panel sliding in from the right with a sticky header, and a body whose direct
// children are the sections, separated by divider lines with the same spacing and type scale
// (15px text, 13px captions, 17px section headings). Keep section content as direct children of the
// shell; a section that renders nothing leaves no divider behind.
export function DrawerShell({
  title, titleId, ariaLabel, onClose, onBack, backLabel = 'Back', dialog, dismissOnOverlay, overlay, children,
}: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/50"
      onMouseDown={dismissOnOverlay ? (event) => { if (event.target === event.currentTarget) onClose() } : undefined}
    >
      <div
        {...(dialog ? { role: 'dialog', 'aria-modal': true, 'aria-labelledby': titleId, 'aria-label': titleId ? undefined : ariaLabel } : {})}
        className="h-full w-full max-w-2xl overflow-y-auto border-l border-[var(--border)] bg-[var(--card)] shadow-xl"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-[var(--border)] bg-[var(--card)] px-8 py-5">
          <div className="flex min-w-0 items-center gap-3">
            {onBack && (
              <button
                type="button"
                aria-label={backLabel}
                onClick={onBack}
                className="text-[var(--text-muted)] hover:text-[var(--text)]"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>
            )}
            <h2 id={titleId} className="min-w-0 break-words text-xl font-semibold text-[var(--text)]">{title}</h2>
          </div>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="shrink-0 text-[var(--text-muted)] hover:text-[var(--text)]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="divide-y divide-[var(--border)] px-8 text-[15px] leading-relaxed text-[var(--text)] [&>*]:py-6">
          {children}
        </div>
      </div>
      {overlay}
    </div>
  )
}
