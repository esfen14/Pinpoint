export type HostRecipients = {
  recipient_ids: number[]
  users: { id: number; name: string; email: string; eligible: boolean }[]
  using_default: boolean
  editable: boolean
}
