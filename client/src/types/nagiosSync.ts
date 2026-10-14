// Fields the acknowledge and unacknowledge routes add to their response data: whether the
// acknowledgement also reached Nagios (see spec "Nagios command channel").
export type NagiosSyncResult = {
  nagios_synced?: boolean
  nagios_message?: string | null
}

// The notice to show, or null when Nagios was updated (or the response says nothing).
export function nagiosSyncNotice(result: NagiosSyncResult | null | undefined): string | null {
  if (!result || result.nagios_synced !== false) return null
  return (
    result.nagios_message ??
    'Saved in PinPoint, but Nagios was not updated. Notifications may continue.'
  )
}
