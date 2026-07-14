#!/usr/bin/env bash
set -euo pipefail

exec /opt/keycloak/bin/kc.sh start \
  --optimized \
  --http-enabled=true \
  --http-port="${PORT:-8080}" \
  --hostname="${KC_HOSTNAME}" \
  --proxy-headers=xforwarded \
  --import-realm
