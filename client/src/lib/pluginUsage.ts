import type { PluginCustomSupport } from '../types/plugin'

// How a plugin is used in Pinpoint, from the backend's capability metadata
// (service_driven and custom_checks). One place, so the inventory and the drawer agree.
export type PluginUsageKind = 'automatic' | 'device' | 'server' | 'nagios' | 'unsupported'

export type PluginUsage = {
  kind: PluginUsageKind
  label: string
  // What the plugin is for, in one sentence.
  summary: string
  // What to do next, or why there is nothing to do.
  nextStep: string
}

type UsageInput = {
  name: string
  service_driven: boolean
  custom_checks?: PluginCustomSupport
}

// Running monitoring is the same for device and server checks; say it once.
export const ONGOING_MONITORING_NOTE =
  'Adding a check starts ongoing monitoring. Inspect its status and output in the list, then pause or remove it.'

export const VALIDATE_NOTE =
  'Validate checks the executable, its permissions, and that it runs with --version. It does not test connectivity, credentials, or an actual monitoring result.'

// Checks of these plugins are written in Nagios Core's own localhost.cfg.
const NAGIOS_MANAGED = new Set(['check_load', 'check_disk', 'check_swap', 'check_procs', 'check_users'])

function stripExtension(name: string) {
  return name.replace(/\.(py|sh|pl)$/i, '')
}

// null while the backend gave nothing to classify with (an older response, or an uploaded plugin).
export function pluginUsage(plugin: UsageInput): PluginUsage | null {
  const custom = plugin.custom_checks
  const name = stripExtension(plugin.name)

  if (plugin.service_driven) {
    return {
      kind: 'automatic',
      label: 'Automatic monitoring',
      summary: 'Monitors the matching ports that network discovery finds.',
      nextStep: 'Enable the plugin to attach monitoring to matching discovered ports. Enable shows a preview first.',
    }
  }
  if (custom?.supported && custom.target === 'server') {
    const password = custom.fields.some((field) => field.secret)
    return {
      kind: 'server',
      label: 'Add server check',
      summary: 'Checks the Nagios server itself.',
      nextStep:
        'Go to Server checks → Add check and enter the required arguments. ' +
        'The check runs on the Nagios server as the Nagios user.' +
        (password ? ' Password fields are write-only.' : ''),
    }
  }
  if (custom?.supported) {
    const password = custom.fields.some((field) => field.secret)
    return {
      kind: 'device',
      label: 'Add device check',
      summary: 'Checks a device you choose, with arguments you enter.',
      nextStep:
        'Go to Custom checks → Add check, choose a device, and enter the required arguments.' +
        (password ? ' The password field is masked and write-only.' : ''),
    }
  }
  if (NAGIOS_MANAGED.has(name) || custom?.class === 'stock') {
    return {
      kind: 'nagios',
      label: 'Managed by Nagios',
      summary: 'Checks the Nagios server through Nagios Core.',
      nextStep: 'Nagios Core manages these server checks. Plugin Manager does not configure them, so there is nothing to enable or add.',
    }
  }
  if (!custom) return null
  return {
    kind: 'unsupported',
    label: 'Not supported yet',
    summary: custom.note ?? 'Pinpoint has no way to use this plugin yet.',
    nextStep: 'No action is available for this plugin.',
  }
}
