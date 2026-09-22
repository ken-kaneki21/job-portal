from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, Field

from jobintel.profile.universal import (
    LLMProfileEnrichment,
    UniversalCandidateProfile,
)

PROMPT_VERSION = "profile_enrichment_v1"


class LLMEnrichmentError(RuntimeError):
    pass


class ProfileEnrichmentOutput(BaseModel):
    suggested_summary: str | None = None
    industries: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    experience_evidence: list[str] = Field(default_factory=list)
    project_evidence: list[str] = Field(default_factory=list)
    role_rationales: dict[str, str] = Field(default_factory=dict)


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    provider: str
    base_url: str
    model: str
    api_key: str
    timeout_seconds: float = 45.0

    @classmethod
    def from_env(cls) -> OpenAICompatibleConfig:
        provider = os.getenv("JOBINTEL_LLM_PROVIDER", "").strip().lower()
        base_url = os.getenv("JOBINTEL_LLM_BASE_URL", "").strip().rstrip("/")
        model = os.getenv("JOBINTEL_LLM_MODEL", "").strip()
        api_key = os.getenv("JOBINTEL_LLM_API_KEY", "").strip()

        if not provider:
            raise LLMEnrichmentError("JOBINTEL_LLM_PROVIDER is missing.")

        if not base_url:
            if provider == "openai":
                base_url = "https://api.openai.com/v1"
            elif provider == "groq":
                base_url = "https://api.groq.com/openai/v1"
            else:
                raise LLMEnrichmentError(
                    "JOBINTEL_LLM_BASE_URL is required for this provider."
                )

        if not model:
            raise LLMEnrichmentError("JOBINTEL_LLM_MODEL is missing.")

        if not api_key:
            raise LLMEnrichmentError("JOBINTEL_LLM_API_KEY is missing.")

        return cls(
            provider=provider,
            base_url=base_url,
            model=model,
            api_key=api_key,
        )


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for value in values:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            continue

        lowered = cleaned.lower()
        if lowered in seen:
            continue

        seen.add(lowered)
        output.append(cleaned)

    return output


def safe_profile_payload(profile: UniversalCandidateProfile) -> dict:
    return {
        "headline": profile.headline,
        "summary": profile.summary,
        "total_experience_years": profile.total_experience_years,
        "role_families": [
            {
                "name": role.name,
                "confidence": role.confidence,
                "priority": role.priority,
                "matched_signals": role.matched_signals,
            }
            for role in profile.role_families
            if role.enabled
        ],
        "core_skills": profile.core_skills,
        "secondary_skills": profile.secondary_skills,
        "tools": profile.tools,
        "cloud_platforms": profile.cloud_platforms,
        "industries": profile.industries,
        "certifications": profile.certifications,
        "experience": [
            {
                "title": entry.title,
                "company": entry.company,
                "description": entry.description,
                "skills": entry.skills,
            }
            for entry in profile.experience
        ],
        "education": [entry.model_dump(mode="json") for entry in profile.education],
        "projects": [entry.model_dump(mode="json") for entry in profile.projects],
    }


def build_prompt(profile: UniversalCandidateProfile) -> str:
    return (
        "You enrich a candidate profile for a private job-intelligence system. "
        "Use only evidence present in the supplied profile. Do not invent skills, "
        "employers, dates, achievements, industries, or experience. "
        "Return a JSON object with exactly these keys: "
        "suggested_summary, industries, tools, experience_evidence, "
        "project_evidence, role_rationales. "
        "industries and tools must be arrays of concise strings. "
        "experience_evidence and project_evidence must contain short factual "
        "evidence statements grounded in the supplied data. "
        "role_rationales must map role-family names to concise evidence-based "
        "rationales. suggested_summary may improve wording but must not add facts. "
        "Candidate profile:\n"
        + json.dumps(
            safe_profile_payload(profile),
            ensure_ascii=False,
        )
    )


def parse_chat_completion(payload: dict) -> ProfileEnrichmentOutput:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMEnrichmentError(
            "LLM response did not contain message content."
        ) from exc

    if not isinstance(content, str):
        raise LLMEnrichmentError("LLM message content was not text.")

    try:
        decoded = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMEnrichmentError("LLM response was not valid JSON.") from exc

    return ProfileEnrichmentOutput.model_validate(decoded)


def request_profile_enrichment(
    profile: UniversalCandidateProfile,
    *,
    config: OpenAICompatibleConfig | None = None,
    client: httpx.Client | None = None,
) -> LLMProfileEnrichment:
    active_config = config or OpenAICompatibleConfig.from_env()

    request_payload = {
        "model": active_config.model,
        "messages": [
            {
                "role": "system",
                "content": "Return only valid JSON. Never invent candidate facts.",
            },
            {
                "role": "user",
                "content": build_prompt(profile),
            },
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    owns_client = client is None
    active_client = client or httpx.Client(
        timeout=active_config.timeout_seconds,
    )

    try:
        response = active_client.post(
            active_config.base_url + "/chat/completions",
            headers={
                "Authorization": "Bearer " + active_config.api_key,
                "Content-Type": "application/json",
            },
            json=request_payload,
        )
        response.raise_for_status()
        output = parse_chat_completion(response.json())
    except httpx.HTTPError as exc:
        raise LLMEnrichmentError("LLM enrichment request failed.") from exc
    finally:
        if owns_client:
            active_client.close()

    return LLMProfileEnrichment(
        provider=active_config.provider,
        model=active_config.model,
        prompt_version=PROMPT_VERSION,
        suggested_summary=output.suggested_summary,
        industries=unique_strings(output.industries),
        tools=unique_strings(output.tools),
        experience_evidence=unique_strings(output.experience_evidence),
        project_evidence=unique_strings(output.project_evidence),
        role_rationales={
            key.strip(): value.strip()
            for key, value in output.role_rationales.items()
            if key.strip() and value.strip()
        },
    )


def apply_profile_enrichment(
    profile: UniversalCandidateProfile,
    enrichment: LLMProfileEnrichment,
    *,
    use_suggested_summary: bool = False,
) -> UniversalCandidateProfile:
    summary = profile.summary

    if use_suggested_summary and enrichment.suggested_summary:
        summary = enrichment.suggested_summary

    return profile.model_copy(
        update={
            "summary": summary,
            "industries": unique_strings(profile.industries + enrichment.industries),
            "tools": unique_strings(profile.tools + enrichment.tools),
            "llm_enrichment": enrichment,
        }
    )
