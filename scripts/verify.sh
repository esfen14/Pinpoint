#!/usr/bin/env bash
# Single verification entry point for agents, developers and CI.
#
# Usage: scripts/verify.sh [docs|backend|frontend|all]   (default: all)
#
# Exits non-zero on the first failing stage. CI runs each stage as its own job
# (.github/workflows/ci.yml) with the same commands, so a green local run means
# a green pipeline. See "spec files/Agent_Workflow_and_CI.md".
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
stage="${1:-all}"

docs() {
  echo "==> docs: relative markdown links (AGENTS.md, README.md, spec files/, docs/, server/tests/)"
  python3 -I "$root/scripts/check_doc_links.py" "$root"
  echo "==> docs: environment variables match the README table"
  python3 -I "$root/scripts/check_env_drift.py"
  echo "==> docs: browser routes match App.tsx, pageAccess.ts and the spec"
  python3 -I "$root/scripts/check_frontend_route_drift.py"
  echo "==> docs: module catalog and requirement mappings align"
  python3 -I "$root/scripts/check_traceability.py"
  echo "==> docs: derived module QA status matches catalog and reviewed evidence"
  python3 -I "$root/scripts/render_qa_case_tables.py" --check
  echo "==> docs: traceability validator contract tests"
  python3 -I "$root/scripts/test_traceability.py"
  echo "==> docs: module/person QA queue selection and freshness"
  python3 -I "$root/scripts/test_qa_queue.py"
  echo "==> docs: module catalog parser contracts"
  python3 -I "$root/scripts/test_qa_catalog.py"
  echo "==> docs: historical evidence reuse contracts"
  python3 -I "$root/scripts/test_qa_evidence.py"
  echo "==> docs: offline execution scope, budget and evidence contracts"
  python3 -I "$root/scripts/test_qa_execute.py"
  echo "==> docs: current-case automation coverage and source-binding contracts"
  python3 -I "$root/scripts/qa_coverage.py" check
  python3 -I "$root/scripts/test_qa_coverage.py"
  echo "==> docs: offline container transport and current-case bypass rejection"
  python3 -I "$root/scripts/test_qa_transport.py"
  echo "==> docs: durable supervisor lifecycle with synthetic driver only"
  python3 -I "$root/scripts/test_qa_supervisor.py"
  python3 -I "$root/scripts/test_qa_recovery.py"
  echo "==> docs: bounded local process groups and strict synthetic report parsing"
  python3 -I "$root/scripts/test_qa_process.py"
  python3 -I "$root/scripts/test_qa_results.py"
  echo "==> docs: concrete container lifecycle with synthetic command responses only"
  python3 -I "$root/scripts/test_qa_container.py"
  echo "==> docs: owned private bridge and read-only deployment observations (fixtures only)"
  python3 -I "$root/scripts/test_qa_bridge.py"
  python3 -I "$root/scripts/test_qa_deployment.py"
  echo "==> docs: composed pilot driver (isolated observers/resources only)"
  python3 -I "$root/scripts/test_qa_pilot.py"
  echo "==> docs: VM control and endpoint ownership safety"
  python3 -I "$root/scripts/test_qa_control.py"
  python3 -I "$root/scripts/test_vmlab_preflight.py"
  echo "==> docs: VM administrator setup compatibility and saved login validation"
  python3 -I "$root/scripts/test_vmlab_setup_admin.py"
  echo "==> docs: isolated defense catalog, input and host preflight contracts (no live lab)"
  python3 -I "$root/demo/defense/test_defense.py"
  python3 -I "$root/demo/defense/test_runtime.py"
  python3 -I "$root/demo/defense/test_guest.py"
  python3 -I "$root/demo/defense/test_provision.py"
  python3 -I "$root/demo/defense/test_hardening.py"
  python3 -I "$root/demo/defense/test_spike.py"
  python3 -I "$root/demo/defense/test_bridge.py"
  python3 -I "$root/demo/defense/test_host_attach.py"
  python3 -I "$root/demo/defense/test_presenter.py"
  python3 -I "$root/demo/defense/test_dhcp_move.py"
  python3 -I "$root/demo/defense/test_dhcp_journal.py"
  python3 -I "$root/demo/defense/test_host_members.py"
  echo "==> docs: agent progress files are well formed"
  python3 -I "$root/scripts/check_agent_progress.py"
  echo "==> docs: fix-found workflow contract"
  python3 -I "$root/scripts/test_fix_found_workflow.py"
}

backend() {
  echo "==> backend: isolated pytest suite"
  cd "$root/server"
  local py=python
  if [ -x .venv/bin/python ]; then py=.venv/bin/python; fi
  echo "==> backend: route catalog matches the Flask routes"
  FLASK_DEBUG=1 "$py" "$root/scripts/check_route_drift.py"
  echo "==> backend: every client /api call matches a Flask route"
  FLASK_DEBUG=1 "$py" "$root/scripts/check_client_api_drift.py"
  FLASK_DEBUG=1 "$py" -m pytest tests/unit -q
}

frontend() {
  echo "==> frontend: test + build"
  cd "$root/client"
  echo "==> frontend: offline current-case selection and Playwright collection (no browser)"
  ./node_modules/.bin/tsc -p tsconfig.qa.json
  node --test qa/selection.node.mjs qa/module-selection.node.mjs qa/timing.node.mjs
  npm run test
  npm run build
  echo "==> frontend: lint (errors block; warnings are tracked in Implementation_Status.md)"
  npm run lint
}

case "$stage" in
  docs) docs ;;
  backend) backend ;;
  frontend) frontend ;;
  all) docs; backend; frontend ;;
  *) echo "unknown stage: $stage" >&2; exit 2 ;;
esac
echo "verify: $stage OK"
