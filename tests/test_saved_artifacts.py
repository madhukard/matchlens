"""Check shipped narratives against the current synthetic evidence snapshot."""

import json

import pytest

from matchlens.domain import MATCH_ID, snapshot
from matchlens.intelligence import Analysis, Narrative, validate_evidence
from matchlens.service import INSIGHTS


@pytest.mark.skipif(not INSIGHTS.exists(), reason="Generate reviewed artifacts first")
def test_shipped_artifacts_have_valid_schemas_and_evidence():
    artifacts = json.loads(INSIGHTS.read_text())
    assert len(artifacts) == 8
    combinations = set()
    for item in artifacts:
        assert item["source"] == "agents_sdk"
        assert item["provider"] in ("azure", "openai")
        assert item["model"]
        data = snapshot(MATCH_ID, **item["window"])
        analysis = Analysis.model_validate(item["analysis"])
        narrative = Narrative.model_validate(item["narrative"])
        for claim in analysis.claims:
            validate_evidence(claim.evidence_event_ids, data)
        validate_evidence(narrative.evidence_event_ids, data)
        combinations.add((item["audience"], item["language"], item["window"]["start_second"]))
    assert combinations == {
        (audience, language, start)
        for audience in ("fan", "analyst")
        for language in ("en", "es")
        for start in (0, 3300)
    }
