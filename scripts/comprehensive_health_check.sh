#!/bin/bash

NAMESPACE=$1

if [ -z "$NAMESPACE" ]; then
  echo "Error: Namespace argument not provided for health check script."
  exit 1
fi

echo "Comprehensive Health Check Script"
echo "Target Namespace: $NAMESPACE"
echo "---"
echo "Placeholder: This script currently replicates the basic service health checks."
echo "Future enhancements should include more in-depth checks (e.g., database connectivity, queue depths, specific API endpoint functionality)."
echo "---"

# Services and their internal ports (as defined in K8s Service objects)
services=("auth-service:8000" "ac-service:8001" "integrity-service:8002" "fv-service:8003" "gs-service:8004" "pgc-service:8005" "workflow-orchestrator:8006")
all_healthy=true

echo "Starting health checks using 'kubectl run curlimages/curl'..."

for service_info in "${services[@]}"; do
  IFS=':' read -r service_name service_port <<< "$service_info"

  echo "Health checking $service_name (port $service_port) in namespace $NAMESPACE..."

  # Using unique pod name for each check to avoid conflicts if run in parallel or retried
  checker_pod_name="health-check-${service_name}-$(date +%s)-${RANDOM}"

  if kubectl run "$checker_pod_name" \
    --rm -i --restart=Never \
    --image=curlimages/curl \
    -n "$NAMESPACE" \
    --command -- curl -s -f "http://${service_name}.${NAMESPACE}.svc.cluster.local:${service_port}/health" --max-time 20; then
    # The service name itself should be resolvable if querying from within a pod in the same namespace.
    # For more robustness, use the FQDN: service_name.namespace.svc.cluster.local
    echo "  ✅ $service_name is healthy."
  else
    echo "  ❌ Health check failed for $service_name in namespace $NAMESPACE."
    # Attempt to get logs from the checker pod if possible (it's --rm, so might be tricky)
    # kubectl logs "$checker_pod_name" -n "$NAMESPACE" --tail=10 || echo "Could not retrieve logs for $checker_pod_name"
    all_healthy=false
  fi
done

echo "---"
if [ "$all_healthy" = true ]; then
  echo "All services in $NAMESPACE are healthy."
  exit 0
else
  echo "One or more services in $NAMESPACE are not healthy."
  exit 1
fi
