// Settings cards that save through their own API (notification policy, escalations) tell the
// Settings configuration summary to refresh, so it never shows a value that was just changed.
const EVENT = 'pinpoint-settings-changed'

export function notifySettingsChanged() {
  window.dispatchEvent(new Event(EVENT))
}

export function onSettingsChanged(listener: () => void) {
  window.addEventListener(EVENT, listener)
  return () => window.removeEventListener(EVENT, listener)
}
