// Inventory tabs. The server owns the category -> tab mapping
// (PLUGIN_GROUP_CATEGORIES in server/app/api/plugin/service.py) and filters on `group`.
export const PLUGIN_GROUPS = [
  'Network Services',
  'Device Availability',
  'Network Protocols',
  'Servers',
  'Application',
  'Other',
] as const

export type PluginGroup = (typeof PLUGIN_GROUPS)[number]
