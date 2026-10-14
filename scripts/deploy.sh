#!/usr/bin/env bash
set -euo pipefail
# Scope every action explicitly; never change the CLI's default subscription.
: "${MATCHLENS_SUBSCRIPTION:?Set the authorized Azure subscription ID}"
: "${MATCHLENS_REGISTRY:?Set a globally unique MatchLens ACR name}"
AZ="${AZ_CLI:-az}"
RG=matchlens-dev-rg
LOCATION="${MATCHLENS_LOCATION:-eastus}"
APP_LOCATION="${MATCHLENS_APP_LOCATION:-westus2}"
TAG="${MATCHLENS_IMAGE_TAG:-$(git rev-parse --short HEAD)}"
"$AZ" group create --subscription "$MATCHLENS_SUBSCRIPTION" -n "$RG" -l "$LOCATION" --tags project=matchlens environment=demo -o none
"$AZ" deployment group create --subscription "$MATCHLENS_SUBSCRIPTION" -g "$RG" -n matchlens-platform-west -f infra/platform.bicep -p registryName="$MATCHLENS_REGISTRY" environmentLocation="$APP_LOCATION" -o none
REGISTRY=$("$AZ" deployment group show --subscription "$MATCHLENS_SUBSCRIPTION" -g "$RG" -n matchlens-platform-west --query properties.outputs.registryServer.value -o tsv)
IDENTITY=$("$AZ" deployment group show --subscription "$MATCHLENS_SUBSCRIPTION" -g "$RG" -n matchlens-platform-west --query properties.outputs.identityId.value -o tsv)
ENVIRONMENT=$("$AZ" deployment group show --subscription "$MATCHLENS_SUBSCRIPTION" -g "$RG" -n matchlens-platform-west --query properties.outputs.environmentId.value -o tsv)
DOMAIN=$("$AZ" deployment group show --subscription "$MATCHLENS_SUBSCRIPTION" -g "$RG" -n matchlens-platform-west --query properties.outputs.defaultDomain.value -o tsv)
"$AZ" acr build --subscription "$MATCHLENS_SUBSCRIPTION" -r "$MATCHLENS_REGISTRY" -t "matchlens:$TAG" .
"$AZ" deployment group create --subscription "$MATCHLENS_SUBSCRIPTION" -g "$RG" -n matchlens-app -f infra/app.bicep -p location="$APP_LOCATION" image="$REGISTRY/matchlens:$TAG" registryServer="$REGISTRY" identityId="$IDENTITY" environmentId="$ENVIRONMENT" publicHost="matchlens-dev.$DOMAIN" --query properties.outputs -o json
