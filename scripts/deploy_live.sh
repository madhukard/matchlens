#!/usr/bin/env bash
set -euo pipefail
AZ="${AZ_CLI:-az}"
SUB="${MATCHLENS_SUBSCRIPTION:?Set the MatchLens subscription}"
RG=matchlens-dev-rg
REGISTRY=matchlensdev1f5dc8
TAG="${MATCHLENS_IMAGE_TAG:?Set a unique image tag}"
MIN_REPLICAS="${MATCHLENS_MIN_REPLICAS:-1}"
[[ "$SUB" == "1f5dc845-2e4c-4a7b-881e-36b5cf032ebb" ]] || { echo 'Wrong subscription'; exit 1; }
"$AZ" deployment group create --subscription "$SUB" -g "$RG" -n matchlens-live -f infra/live.bicep --only-show-errors -o none
IDENTITY=$("$AZ" identity show --subscription "$SUB" -g "$RG" -n matchlens-dev-runtime --query id -o tsv)
CLIENT=$("$AZ" identity show --subscription "$SUB" -g "$RG" -n matchlens-dev-runtime --query clientId -o tsv)
WORKER=$("$AZ" identity show --subscription "$SUB" -g "$RG" -n matchlens-dev-worker --query id -o tsv)
WORKER_CLIENT=$("$AZ" identity show --subscription "$SUB" -g "$RG" -n matchlens-dev-worker --query clientId -o tsv)
ENVIRONMENT=$("$AZ" containerapp env show --subscription "$SUB" -g "$RG" -n matchlens-dev-env-west --query id -o tsv)
DOMAIN=$("$AZ" containerapp env show --subscription "$SUB" -g "$RG" -n matchlens-dev-env-west --query properties.defaultDomain -o tsv)
STORAGE=https://matchlenslive1f5dc8.blob.core.windows.net/
IMAGE="$REGISTRY.azurecr.io/matchlens:$TAG"
"$AZ" acr build --subscription "$SUB" -r "$REGISTRY" -t "matchlens:$TAG" . --only-show-errors
"$AZ" deployment group create --subscription "$SUB" -g "$RG" -n matchlens-app -f infra/app.bicep -p image="$IMAGE" registryServer="$REGISTRY.azurecr.io" identityId="$IDENTITY" environmentId="$ENVIRONMENT" publicHost="matchlens-dev.$DOMAIN" storageUrl="$STORAGE" clientId="$CLIENT" minReplicas="$MIN_REPLICAS" --only-show-errors -o none
"$AZ" deployment group create --subscription "$SUB" -g "$RG" -n matchlens-worker -f infra/worker.bicep -p image="$IMAGE" registryServer="$REGISTRY.azurecr.io" identityId="$WORKER" clientId="$WORKER_CLIENT" environmentId="$ENVIRONMENT" storageUrl="$STORAGE" --only-show-errors -o none
echo "Deployed https://matchlens-dev.$DOMAIN; worker is manual-only and not started."
