#!/usr/bin/env bash
# Presenter controls for the isolated defense demo lab (fourteen Linux targets).
# Works from the repository or through a symlink (e.g. ~/Documents/Pinpoint-Demo/).
set -euo pipefail

here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
demo="$here/demo"

usage() {
  cat <<'HELP'
Usage: Pinpoint-Demo-faults.sh status|wall|services TARGET
       Pinpoint-Demo-faults.sh down|up TARGET SERVICE|host
       Pinpoint-Demo-faults.sh dhcp-move DHCP_TARGET 10.77.1.N | dhcp-recover
       Pinpoint-Demo-faults.sh ports list TARGET | open TARGET http|tcp PORT | close TARGET PORT | restore TARGET|all

Static targets:  dhcp01 web03 api02 ftp01 mail01 dns01 db01 snmp02 ssh-alt02
DHCP targets:    dynweb01 dynapp01 dynmail01 dynsnmp01 dynweb02
SERVICE per target (host = stop/start the whole container):
  web03: http https   api02: http   ftp01: ftp   mail01: smtp imap
  dns01: dns   db01: pgsql   snmp02: snmp   dhcp01, ssh-alt02: ssh
  dynweb01 dynapp01 dynweb02: ssh http   dynmail01: ssh smtp   dynsnmp01: ssh snmp

Examples:
  Pinpoint-Demo-faults.sh down web03 http      # one monitored service fails
  Pinpoint-Demo-faults.sh up web03 http        # restore it
  Pinpoint-Demo-faults.sh down dynapp01 host   # stop one container
  Pinpoint-Demo-faults.sh dhcp-move dynweb01 10.77.1.25   # change its lease; move back with .20
  Pinpoint-Demo-faults.sh dhcp-recover         # only after an interrupted move
  Pinpoint-Demo-faults.sh ports open web03 http 8088   # extra port; close it with: ports close web03 8088
  Pinpoint-Demo-faults.sh ports restore all    # close every extra port (end of demo)

Only use these controls with the disposable defense demo lab. Windows (win01) has
no controls here.
HELP
}

fail() { usage >&2; exit 2; }

presenter() { exec "$demo" presenter "$@"; }

valid_target() {
  case "$1" in
    dhcp01|web03|api02|ftp01|mail01|dns01|db01|snmp02|ssh-alt02|dynweb01|dynapp01|dynmail01|dynsnmp01|dynweb02) return 0 ;;
  esac
  return 1
}

valid_service() {
  case "$1:$2" in
    web03:http|web03:https|api02:http|ftp01:ftp|mail01:smtp|mail01:imap|dns01:dns|db01:pgsql|snmp02:snmp) return 0 ;;
    dhcp01:ssh|ssh-alt02:ssh|dynweb01:ssh|dynweb01:http|dynapp01:ssh|dynapp01:http) return 0 ;;
    dynmail01:ssh|dynmail01:smtp|dynsnmp01:ssh|dynsnmp01:snmp|dynweb02:ssh|dynweb02:http) return 0 ;;
  esac
  return 1
}

[[ -x "$demo" ]] || { printf 'Missing demo command: %s\n' "$demo" >&2; exit 1; }

action="${1:-}"
case "$action" in
  status)
    [[ $# -eq 1 ]] || fail
    presenter status
    ;;
  wall)
    [[ $# -eq 1 ]] || fail
    while true; do
      clear
      "$demo" presenter status || true
      sleep 3
    done
    ;;
  services)
    [[ $# -eq 2 ]] || fail
    valid_target "$2" || fail
    "$demo" presenter status | awk -v target="$2" '$1 == target'
    ;;
  down|up)
    [[ $# -eq 3 ]] || fail
    valid_target "$2" || fail
    if [[ "$3" == host ]]; then
      if [[ "$action" == down ]]; then presenter host-stop "$2"; fi
      presenter host-start "$2"
    fi
    valid_service "$2" "$3" || fail
    if [[ "$action" == down ]]; then presenter break "$2" "$3"; fi
    presenter fix "$2" "$3"
    ;;
  dhcp-move)
    [[ $# -eq 3 ]] || fail
    case "$2" in dynweb01|dynapp01|dynmail01|dynsnmp01|dynweb02) ;; *) fail ;; esac
    [[ "$3" =~ ^10\.77\.1\.[0-9]{1,2}$ ]] || fail
    presenter dhcp-move "$2" "$3"
    ;;
  ports)
    case "${2:-}" in
      list)
        [[ $# -eq 3 ]] || fail
        valid_target "$3" || fail
        presenter ports list "$3"
        ;;
      open)
        [[ $# -eq 5 ]] || fail
        valid_target "$3" || fail
        case "$4" in http|tcp) ;; *) fail ;; esac
        [[ "$5" =~ ^[0-9]{4,5}$ ]] || fail
        presenter ports open "$3" "$4" "$5"
        ;;
      close)
        [[ $# -eq 4 ]] || fail
        valid_target "$3" || fail
        [[ "$4" =~ ^[0-9]{4,5}$ ]] || fail
        presenter ports close "$3" "$4"
        ;;
      restore)
        [[ $# -eq 3 ]] || fail
        if [[ "$3" != all ]]; then valid_target "$3" || fail; fi
        presenter ports restore "$3"
        ;;
      *) fail ;;
    esac
    ;;
  dhcp-recover)
    [[ $# -eq 1 ]] || fail
    presenter dhcp-recover
    ;;
  help|-h|--help) usage ;;
  *) fail ;;
esac
