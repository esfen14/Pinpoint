import { DropdownSelect } from '../shared/DropdownSelect'

interface SettingsSelectOption { value: string; label: string }
interface SettingsSelectProps {
  label: string; value: string; options: SettingsSelectOption[]
  onChange: (value: string) => void; description?: string
}

// A labelled form-field dropdown: the same button-and-list control as the rest of the app
// (shared/DropdownSelect), stretched to the field width.
export function SettingsSelect({ label, value, options, onChange, description }: SettingsSelectProps) {
  return (
    <div>
      <span className="mb-2 block text-sm font-medium text-[var(--text)]">{label}</span>
      <DropdownSelect block label={label} value={value} options={options} onChange={onChange} />
      {description && <p className="mt-1.5 text-xs text-[var(--text-muted)]">{description}</p>}
    </div>
  )
}
