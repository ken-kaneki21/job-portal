from __future__ import annotations

from jobintel.profile.llm_enrichment import (
    ProfileEnrichmentOutput,
    apply_profile_enrichment,
    build_prompt,
    parse_chat_completion,
)
from jobintel.profile.universal import (
    LLMProfileEnrichment,
    UniversalCandidateProfile,
)


def test_prompt_excludes_identity_pii():
    profile = UniversalCandidateProfile(
        profile_name="universal",
    )
    profile.identity.email = "private@example.com"

    prompt = build_prompt(profile)

    assert "private@example.com" not in prompt


def test_parse_chat_completion():
    result = parse_chat_completion(
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"suggested_summary":"Data engineer",'
                            '"industries":["Healthcare"],'
                            '"tools":["Temporal"],'
                            '"experience_evidence":["Built pipelines"],'
                            '"project_evidence":["Built JobLens"],'
                            '"role_rationales":{"Data Engineer":"ETL"}}'
                        )
                    }
                }
            ]
        }
    )

    assert isinstance(result, ProfileEnrichmentOutput)
    assert result.industries == ["Healthcare"]


def test_apply_profile_enrichment_is_additive():
    profile = UniversalCandidateProfile(
        profile_name="universal",
        summary="Deterministic summary",
        tools=["Docker"],
    )

    enrichment = LLMProfileEnrichment(
        provider="test",
        model="test-model",
        prompt_version="v1",
        suggested_summary="Suggested summary",
        industries=["Healthcare"],
        tools=["Docker", "Temporal"],
    )

    enriched = apply_profile_enrichment(
        profile,
        enrichment,
    )

    assert enriched.summary == "Deterministic summary"
    assert enriched.tools == ["Docker", "Temporal"]
    assert enriched.industries == ["Healthcare"]
    assert enriched.llm_enrichment == enrichment
