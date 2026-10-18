import { useEffect } from 'react'

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

// Escape closes, Tab stays inside the open dialog, and focus returns to the
// control that opened it. DrawerShell renders the dialog; this finds it by role.
export function useDialogFocus(onClose: () => void) {
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null
    const dialog = () => document.querySelector<HTMLElement>('[role="dialog"]')
    dialog()?.querySelector<HTMLElement>(FOCUSABLE)?.focus()

    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.stopPropagation()
        onClose()
        return
      }
      if (event.key !== 'Tab') return
      const root = dialog()
      const items = root ? Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)) : []
      if (items.length === 0) return
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      opener?.focus?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}
