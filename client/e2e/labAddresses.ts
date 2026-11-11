// Address prefixes of the current labs. The earlier five-VM lab was removed (#298).
// Demo lab (demo/README.md): 10.77.1.0/27. Local Docker lab (docs/manuals/Local_Lab.md): 10.78.0.0/24.
const LAB_HOST_PREFIXES = ['10.77.1.', '10.78.0.']

export function isLabAddress(address: string | null | undefined): boolean {
  if (!address) return false
  for (const prefix of LAB_HOST_PREFIXES) {
    if (address.startsWith(prefix)) return true
  }
  return false
}
