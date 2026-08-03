#!/usr/bin/env bash
set -euo pipefail

PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_toolkit.py
PYTHONDONTWRITEBYTECODE=1 python3 skills/mobile-app-ship/scripts/validate_playbook.py
if [[ "${CI:-}" == "true" ]]; then
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_onboarding_browser.py
fi
