# Azure deployment and operations

The first deployment uses the same subscription as Dhisana, **Dhisana AI Development**, in a NEW resource group, **matchlens-dev-rg**. The resource group, registry and AI account are in eastus; the serving environment and app are in westus2. Existing Dhisana resource groups, services, identities, DNS and databases are not dependencies and were not modified.

Resources:

- `matchlens-dev-ai-1f5dc8`: separate Azure OpenAI account; `gpt-6-sol` version `2026-09-22`, GlobalStandard, capacity 60. Used by the authenticated manual synthetic-stream worker.
- `matchlensdev1f5dc8`: Basic Container Registry, admin password disabled.
- `matchlens-dev-runtime`: managed identity with AcrPull on the new registry and Blob Data Reader on the private run container.
- `matchlens-dev-env-west`: consumption Container Apps environment in westus2.
- `matchlens-dev`: HTTPS app, 0–1 replica, 0.25 CPU and 0.5 GiB RAM. Contains saved demo artifacts, no model credentials.

`infra/platform.bicep`, `infra/app.bicep` and `infra/ai.bicep` describe the resources. `scripts/deploy.sh` rebuilds the serving image and updates only the new resource group. The AI template is separate because normal web deployments should not change model deployments. Region/model quota must be available.

```sh
export MATCHLENS_SUBSCRIPTION='<authorized subscription ID>'
export MATCHLENS_REGISTRY=matchlensdev1f5dc8
./scripts/deploy.sh
```

Regenerate and review `matchlens/data/insights.json` before rebuilding when the evidence or prompts change. CI runs tests only and has no Azure deployment credentials. This avoids automatic infrastructure changes from a code push.

## Costs and access

No monthly budget amount was supplied, so no arbitrary budget or hard spending cap is claimed. Scale-to-zero and a single-replica limit constrain serving costs but are **not spending caps**. ACR has a recurring Basic charge; builds, model generation, network egress and active compute may incur charges. The model is pay-per-token GlobalStandard, not provisioned throughput. Set a resource-group budget and alerts once the owner chooses an amount; Azure budget alerts themselves do not stop spending.

The public `/mcp` and preview expose fictional demo data only. Tools cannot invoke paid models, write files, fetch arbitrary URLs or change infrastructure. Do not add private match feeds or customer records until OAuth and per-user authorization are implemented. Browser UI uses host MCP calls rather than exposing Azure credentials. MCP requests retain allowed-host and origin validation.

For rollback, redeploy `infra/app.bicep` with a previously tested immutable image tag. Health is `/health`; MCP is `/mcp`. A cold start is possible at zero replicas. To retire the demo, review and remove only `matchlens-dev-rg` through your normal Azure process; never run cleanup against a Dhisana group.

The initial eastus serving environment remained queued and was retired after westus2 provisioned successfully. The 14 October resource inventory no longer lists the unused eastus environment. This was contained within the new MatchLens resource group.

## Live worker operations

`infra/live.bicep` provisions private storage `matchlenslive1f5dc8` and separate worker identity `matchlens-dev-worker`. `infra/worker.bicep` provisions manual job `matchlens-live-worker` (1,200-second timeout, no automatic job retry). Only this identity has the MatchLens inference role and write access to its run container. A renewable blob lease rejects concurrent publishers.

Deploy without starting generation:

```sh
MATCHLENS_IMAGE_TAG=<unique-release-tag> bash scripts/deploy_live.sh
```

Start one bounded synthetic run with the authorized Azure operator account:

```sh
az containerapp job start --subscription "$MATCHLENS_SUBSCRIPTION" --resource-group matchlens-dev-rg --name matchlens-live-worker
```

Watch execution state and inspect `/api/run` for frame status, evidence and trace. A successful job exit alone does not mean every narrative passed review: inspect all six frames. Do not run evaluation concurrently with this job; both consume the same model quota. No automatic schedule or public generation trigger exists.

Generation reserves up to 600,000 conservative tokens / 48 calls per stream. A four-case paired evaluation reserves up to 1,200,000 / 64 calls, including advisory graders. These reservations and the 60,000 tokens/minute model throughput limit are different controls. Neither establishes a monthly dollar cap. Failed calls may still consume quota; each explicit retry reserves budget again.

For a hung execution, use the Azure job's stop operation scoped to `matchlens-live-worker` and the exact execution name. Do not delete or modify any Dhisana resources. A bundled recorded run supports read-only judging when Blob retrieval is unavailable and is labelled as a recording.
