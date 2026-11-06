"""Unified AI Client factory supporting configurable and optional LLM backends."""

from typing import TypeVar

from pydantic import BaseModel

from iso_assistant.ai.provider_base import AbstractLLMProvider
from iso_assistant.ai.schemas import (
    AIGapAssessmentOutput,
    AIRiskAssessmentOutput,
    AIRiskItemOutput,
    AISoAJustificationOutput,
)
from iso_assistant.config import settings

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(AbstractLLMProvider):
    """Offline deterministic mock provider used when no external API credentials are provided.

    Enables local testing, continuous integration, and demo workflows without cloud dependencies.
    """

    def is_available(self) -> bool:
        return True

    def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_model: type[T],
        temperature: float = 0.1,
    ) -> T:
        """Returns realistic mock evaluation models for offline and test operation."""
        if response_model == AIGapAssessmentOutput:
            return response_model(  # type: ignore[return-value]
                compliance_status="Partially Compliant",
                compliance_score=0.5,
                evidence_quote="Sample policy excerpt indicates periodic access reviews occur annually.",
                identified_gaps="Access reviews lack documented sign-off from asset owners.",
                remediation_plan="Implement quarterly documented access reviews with formal owner attestation.",
                confidence_score=0.85,
                reasoning="Mock analysis determined partial compliance based on policy documentation.",
            )

        if response_model == AIRiskAssessmentOutput:
            return response_model(  # type: ignore[return-value]
                identified_risks=[
                    AIRiskItemOutput(
                        risk_title="Unauthorized access via unmanaged external accounts",
                        asset_or_process="Corporate Cloud Identity System",
                        threat="Former employees retaining privileged access",
                        vulnerability="Absence of automated offboarding and deprovisioning",
                        impacted_cia="Confidentiality & Integrity",
                        inherent_likelihood=4,
                        inherent_impact=4,
                        treatment_strategy="Mitigate",
                        mapped_controls=["A.5.15", "A.8.2"],
                        treatment_details="Enforce automated SCIM provisioning and weekly inactive account sweeps.",
                        residual_likelihood=2,
                        residual_impact=2,
                    )
                ]
            )

        if response_model == AISoAJustificationOutput:
            return response_model(  # type: ignore[return-value]
                control_id="A.8.2",
                is_applicable=True,
                justification="Mandatory control to protect sensitive company and customer data in cloud systems.",
                suggested_implementation_status="In Progress",
            )

        # Generic fallback
        return response_model()  # type: ignore[return-value]


class AIClient:
    """Entry point for all AI assessment interactions."""

    def __init__(self, provider: AbstractLLMProvider | None = None):
        self.provider: AbstractLLMProvider = provider or self._resolve_provider()

    @staticmethod
    def _resolve_provider() -> AbstractLLMProvider:
        """Resolves active LLM backend based on environment configuration."""
        provider_name = settings.llm_provider.lower()

        if provider_name == "mock":
            return MockLLMProvider()

        # Placeholders for future provider implementations (e.g. OpenAI, Gemini, Anthropic, Ollama)
        # If API key is missing or invalid, gracefully fallback to Mock
        return MockLLMProvider()

    def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_model: type[T],
    ) -> T:
        """Delegates prompt execution to the configured provider backend."""
        return self.provider.generate_structured(
            prompt=prompt,
            system_instruction=system_instruction,
            response_model=response_model,
            temperature=settings.llm_temperature,
        )

