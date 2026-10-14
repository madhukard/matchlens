# Azure deployment and operations

The first deployment uses the same subscription as Dhisana, **Dhisana AI Development**, in a NEW resource group, **matchlens-dev-rg**, eastus. Existing Dhisana resource groups, services, identities, DNS and databases are not dependencies and were not modified.

Resources:

- `matchlens-dev-ai-1f5dc8`: separate Azure OpenAI account; `gpt-6-sol` version `2026-09-22`, GlobalStandard, capacity 10. Used for offline synthetic narrative generation only.
- `matchlensdev1f5dc8`: Basic Container Registry, admin password disabled.
- `matchlens-dev-runtime`: managed identity with AcrPull scoped to that new registry only.
- `matchlens-dev-env`: consumption Container Apps environment.
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
