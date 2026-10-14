# Verification — 14 October 2026

## Automated and protocol checks

- 36 Python tests pass. Coverage includes exact statistics, future-event boundaries, duplicate/late delivery, revision conflicts, score retraction, superseded and cross-run citations, structured MCP UI results, read-only export, reviewer feedback propagation, bounded rate-limit retry, budget reservation and statistics-only fallback.
- Ruff and JavaScript syntax checks pass. Installed dependencies pass consistency checking. A focused credential-pattern scan of 62 repository files found no potential embedded secrets; this is not an exhaustive security audit.
- The official MCP Python client passes discovery of nine tools, structured invocation, evidence checks, UI resource retrieval and invalid-input checks on the public Azure endpoint.
- The final paired evaluation records multi-agent 4/4 packages passing publication gates versus single-agent 2/4, with higher latency/token usage. See `evaluation.md` for full conditions, earlier trials and limits.

## Browser and host checks

Chrome checks verified the public score and goal correction, audience/language controls, a 390px viewport without horizontal overflow, and no visible application error. The local MCP Apps harness verified initialization, host tool calls, light-theme context, Spanish rendering and selected-event context containing the corrected `finish-4@2`, run ID and evidence hash. Unchanged background polling preserves the selected view.

The private ChatGPT plugin listing is version 0.2.0, release `pluginrel_6acfe6db4d148191a6288a6234c60e97`, plugin `plugins_6acfdfe899388191af6dc5741e611de1`. Actual native conversation rendering is still awaiting the owner's manual acceptance check; the harness is not a substitute.

Claude Code 2.1.300 is installed through its official npm package but reports `loggedIn: false`; website authentication did not authenticate the CLI. No Claude Code end-to-end pass is claimed.

GitHub Copilot CLI 1.0.98 was tested with the MatchLens MCP configuration. Organization policy explicitly blocked third-party MCP servers. The account administrator must resolve permitted access; no policy bypass or Copilot success is claimed. VS Code Copilot and Copilot Studio have not been independently accepted.

## Azure evidence

All changes are scoped to `matchlens-dev-rg`. The inventory contains dedicated AI, registry, serving/worker identities, storage, environment, app and manual job resources. The abandoned eastus environment is absent from the current inventory. The serving app has no inference key or inference role; the worker's managed identity successfully invokes the dedicated model and publishes to private storage.

The first worker run encountered rate limits while evaluation ran concurrently. RC3 then completed with five approved frames and one correctly withheld pressure narrative. The verifier caught pass-attempt/completion and event-order claims. This led to the editor-feedback regression fix and another serialized validation run. A successful job exit is never treated as proof that all narratives were approved.

Final six-frame acceptance and the final immutable image digest are recorded below after completion. The reproducible check is `python scripts/verify_live.py <demo-base-url> --save matchlens/data/live.json`.

### Final live run accepted

Execution `matchlens-live-worker-3pdjzub`, run `c34edcdf-2daa-4bcc-a7b4-7ef3a0c052a1`, completed at 2026-10-14 20:52:08 UTC. All six frames passed both reviews. Frame generation times: 17.676, 13.993, 14.233, 21.174, 20.662 and 20.869 seconds. The public acceptance script verified all 24 audience/language combinations, 1–0 at frame 4, 0–0 at frame 5, rejection of the superseded goal ID, and rejection of a different run ID. The full ledger is bundled in `matchlens/data/live.json` for an explicitly labelled recording fallback.
