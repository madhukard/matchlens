# Verification — 14 October 2026

## Automated and protocol checks

- 36 Python tests pass. Coverage includes exact statistics, future-event boundaries, duplicate/late delivery, revision conflicts, score retraction, superseded and cross-run citations, structured MCP UI results, read-only export, reviewer feedback propagation, bounded rate-limit retry, budget reservation and statistics-only fallback.
- Ruff and JavaScript syntax checks pass. Installed dependencies pass consistency checking. A focused credential-pattern scan of 62 repository files found no potential embedded secrets; this is not an exhaustive security audit.
- The official MCP Python client passes discovery of nine tools, structured invocation, evidence checks, UI resource retrieval and invalid-input checks on the public Azure endpoint.
- The final paired evaluation records multi-agent 4/4 packages passing publication gates versus single-agent 2/4, with higher latency/token usage. See `evaluation.md` for full conditions, earlier trials and limits.

## Browser and host checks

Chrome checks verified the public score and goal correction, audience/language controls, a 390px viewport without horizontal overflow, and no visible application error. The local MCP Apps harness verified initialization, host tool calls, light-theme context, Spanish rendering and selected-event context containing the corrected `finish-4@2`, run ID and evidence hash. Unchanged background polling preserves the selected view.

The private ChatGPT plugin listing is version 0.2.0, release `pluginrel_6acfe6db4d148191a6288a6234c60e97`, plugin `plugins_6acfdfe899388191af6dc5741e611de1`. Actual native conversation rendering is still awaiting the owner's manual acceptance check; the harness is not a substitute.

Claude Code 2.1.300 authenticated successfully and passed a restricted live MCP test on 14 October 2026. It connected to the Azure endpoint, called `get_live_match` for frames 4 and 5, reported 1–0 then 0–0, observed rejection of superseded `finish-4@1` at frame 5, and fetched current `finish-4@2`. No local file or shell tools were available and there were no permission denials. This verifies terminal tool use, not embedded graphical rendering. See `claude-acceptance.json` for the sanitized call summary.

GitHub Copilot CLI 1.0.98 was tested with the MatchLens MCP configuration. Organization policy explicitly blocked third-party MCP servers. The account administrator must resolve permitted access; no policy bypass or Copilot success is claimed. VS Code Copilot and Copilot Studio have not been independently accepted.

## Azure evidence

All changes are scoped to `matchlens-dev-rg`. The inventory contains dedicated AI, registry, serving/worker identities, storage, environment, app and manual job resources. The abandoned eastus environment is absent from the current inventory. The serving app has no inference key or inference role; the worker's managed identity successfully invokes the dedicated model and publishes to private storage.

The first worker run encountered rate limits while evaluation ran concurrently. RC3 then completed with five approved frames and one correctly withheld pressure narrative. The verifier caught pass-attempt/completion and event-order claims. This led to the editor-feedback regression fix and another serialized validation run. A successful job exit is never treated as proof that all narratives were approved.

Final six-frame acceptance and the final immutable image digest are recorded below after completion. The reproducible check is `python scripts/verify_live.py <demo-base-url> --save matchlens/data/live.json`.

### Final live run accepted

Execution `matchlens-live-worker-3pdjzub`, run `c34edcdf-2daa-4bcc-a7b4-7ef3a0c052a1`, completed at 2026-10-14 20:52:08 UTC. All six frames passed both reviews. Frame generation times: 17.676, 13.993, 14.233, 21.174, 20.662 and 20.869 seconds. The public acceptance script verified all 24 audience/language combinations, 1–0 at frame 4, 0–0 at frame 5, rejection of the superseded goal ID, and rejection of a different run ID. The full ledger is bundled in `matchlens/data/live.json` for an explicitly labelled recording fallback.

### Released artifact

- Image: `matchlensdev1f5dc8.azurecr.io/matchlens:v0.2.0`
- Digest: `sha256:25f0ca75ccc5081c270f4a6dc08e5dd3f9c37773d2e4ebf4e384070add3d7458`
- Ready Azure revision: `matchlens-dev--0000004`; provisioning state Succeeded.
- Public MCP smoke and the six-frame / 24-variant acceptance script passed again against this final release.
- Implementation commit `1c9c35a` passed [GitHub Actions](https://github.com/madhukard/matchlens/actions/runs/38636264771).
- Focused credential-pattern scans found no potential embedded secrets in 62 working-tree files or 99 history blobs. This does not establish an exhaustive security audit.
- The 1:53 H.264 demo was decoded for duration and opening/middle/closing frame inspection. It has English captions and no audio. The opening is a labelled replay still; the main sequence is actual Azure UI capture; the closing trace is held for the evaluation caption.

## Final evaluator review

The strongest category evidence is the revision-aware correction path, explicit agent responsibilities, retained rejection history, recoverable handoffs and paired baseline. Technical and presentation evidence now supports a credible demonstration. The main competitive limitation is the small authored scenario: this is not licensed, continuous match ingestion, and the same-model reviewer/grader setup is not independent assurance. The additional calls demonstrably cost latency and tokens.

The repository is public following explicit owner authorization. Submission remains gated on accepted public video hosting, owner-confirmed entrant details and final portal review. Native ChatGPT acceptance remains pending, and Copilot is blocked by organization policy as described above; Claude Code tool acceptance passed. Do not label the complete requested integration scope or the competition submission “100% ready” while these gates are open.
