#!/bin/bash
# Health check integration test
# Usage: ./health_check.sh <alb-dns-name>

set -e

ALB_URL="${1:-localhost:8080}"
MAX_RETRIES=10
RETRY_INTERVAL=15

echo "============================================"
echo "  Integration Health Check"
echo "  Target: http://$ALB_URL"
echo "============================================"

# ── Test 1: /health endpoint ──────────────────────────────────────────────────
echo ""
echo "[1/2] Testing /health endpoint..."

for i in $(seq 1 $MAX_RETRIES); do
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$ALB_URL/health" || echo "000")

  if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "  PASS /health returned HTTP 200"
    break
  fi

  echo "  Attempt $i/$MAX_RETRIES — got HTTP $HTTP_STATUS, retrying in ${RETRY_INTERVAL}s..."
  sleep $RETRY_INTERVAL

  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "  FAIL /health did not return 200 after $MAX_RETRIES attempts"
    exit 1
  fi
done

# ── Test 2: /health response body ────────────────────────────────────────────
echo ""
echo "[2/2] Testing /health response body..."

BODY=$(curl -s "http://$ALB_URL/health")

if echo "$BODY" | grep -q '"status"'; then
  echo "  PASS response contains 'status' key: $BODY"
else
  echo "  FAIL unexpected response body: $BODY"
  exit 1
fi

echo ""
echo "============================================"
echo "  All health checks PASSED"
echo "  App is live at: http://$ALB_URL"
echo "============================================"
