#!/bin/bash
# Pre-Deployment IAM & Resource Auditor
# Enforces set -euo pipefail standard

set -euo pipefail

echo -e "\033[94m============================================================\033[0m"
echo -e "\033[94m          🚀 GCP PRE-DEPLOYMENT IAM VALIDATION GATE          \033[0m"
echo -e "\033[94m============================================================\033[0m"

# 1. Fetch current deployer identity
DEPLOYER_EMAIL=$(gcloud config get-value account 2>/dev/null || true)
if [ -z "$DEPLOYER_EMAIL" ]; then
    echo -e "\033[91m[Error] No active gcloud account found. Run 'gcloud auth login'.\033[0m"
    exit 1
fi
echo -e "[GCP-Preflight] Active Deployer: $DEPLOYER_EMAIL"

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
if [ -z "$PROJECT_ID" ]; then
    echo -e "\033[91m[Error] No active gcloud project set. Run 'gcloud config set project [PROJECT]'.\033[0m"
    exit 1
fi
echo -e "[GCP-Preflight] Target Project: $PROJECT_ID"

# 2. Check for Wildcard Security Policies (Risk Auditing)
echo -e "[GCP-Preflight] Auditing IAM policy bindings for wildcard roles..."
WILDCARD_ROLES=$(gcloud projects get-iam-policy "$PROJECT_ID" \
  --filter="bindings.members:$DEPLOYER_EMAIL AND (bindings.role:roles/owner OR bindings.role:roles/editor)" \
  --format="value(bindings.role)" 2>/dev/null || true)

if [ -n "$WILDCARD_ROLES" ]; then
    echo -e "  - \033[91m[WARNING]\033[0m Account holds wildcard roles: $WILDCARD_ROLES"
    echo -e "    * Recommendation: Transition to predefined roles (e.g. roles/run.admin, roles/iam.serviceAccountUser)"
else
    echo -e "  - \033[92m[PASS]\033[0m No wildcard roles detected (Least-Privilege met)."
fi

# 3. Verify Required Cloud Run Deployment Roles
echo -e "[GCP-Preflight] Verifying required deployment roles..."
REQUIRED_ROLES=("roles/run.admin" "roles/iam.serviceAccountUser")
PASS_COUNT=0

ACTIVE_ROLES=$(gcloud projects get-iam-policy "$PROJECT_ID" \
  --filter="bindings.members:$DEPLOYER_EMAIL" \
  --format="value(bindings.role)" 2>/dev/null || true)

for role in "${REQUIRED_ROLES[@]}"; do
    if echo "$ACTIVE_ROLES" | grep -q "$role"; then
        echo -e "  - \033[92m[PASS]\033[0m Deployer holds $role"
        PASS_COUNT=$((PASS_COUNT+1))
    else
        echo -e "  - \033[93m[MISSING]\033[0m Deployer lacks $role (Deployment may fail!)"
    fi
done

if [ "$PASS_COUNT" -lt "${#REQUIRED_ROLES[@]}" ]; then
    echo -e "\033[93m[Preflight Summary] Core deployment permissions are incomplete. Proceed with caution.\033[0m"
    exit 2
else
    echo -e "\033[92m[Preflight Summary] All core IAM policies validated. Deployment is safe to proceed.\033[0m"
    exit 0
fi
