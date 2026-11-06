"""Pydantic schemas for LLM structured output parsing and validation."""

from typing import Literal

from pydantic import BaseModel, Field


class AIGapAssessmentOutput(BaseModel):
    """Structured response model for an AI draft evaluation of an ISO 27001 control."""

    compliance_status: Literal["Compliant", "Partially Compliant", "Non-Compliant", "Not Applicable"] = Field(
        description="Assessed compliance state based solely on available evidence",
    )
    compliance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Quantified compliance score (1.0 = full, 0.5 = partial, 0.0 = non-compliant)",
    )
    evidence_quote: str = Field(
        description="Direct citation or excerpt from the uploaded documentation substantiating the finding",
    )
    identified_gaps: str = Field(
        description="Detailed description of missing controls, procedures, or evidence",
    )
    remediation_plan: str = Field(
        description="Actionable, prioritized recommendations to achieve full compliance",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Model self-estimated confidence score based on clarity of evidence",
    )
    reasoning: str = Field(
        description="Chain-of-thought analysis explaining why this status was selected",
    )


class AIRiskItemOutput(BaseModel):
    """Structured representation of an individual information security risk."""

    risk_title: str = Field(description="Concise description of the risk scenario")
    asset_or_process: str = Field(description="Affected organizational asset, system, or process")
    threat: str = Field(description="Potential threat actor or event causing harm")
    vulnerability: str = Field(description="Specific weakness or absence of safeguard")
    impacted_cia: str = Field(description="Impacted information security property (C, I, A, or combo)")
    inherent_likelihood: int = Field(ge=1, le=5, description="Likelihood score from 1 (Rare) to 5 (Almost Certain)")
    inherent_impact: int = Field(ge=1, le=5, description="Impact score from 1 (Insignificant) to 5 (Catastrophic)")
    treatment_strategy: Literal["Mitigate", "Avoid", "Transfer", "Accept"] = Field(
        description="Recommended ISO 27005 treatment strategy",
    )
    mapped_controls: list[str] = Field(
        description="ISO 27001:2022 control IDs that mitigate this risk (e.g. ['A.5.15', 'A.8.2'])",
    )
    treatment_details: str = Field(description="Concrete action plan to reduce likelihood or impact")
    residual_likelihood: int = Field(ge=1, le=5, description="Expected residual likelihood after treatment")
    residual_impact: int = Field(ge=1, le=5, description="Expected residual impact after treatment")


class AIRiskAssessmentOutput(BaseModel):
    """Container schema for batch risk identification results."""

    identified_risks: list[AIRiskItemOutput] = Field(
        description="List of identified information security risks discovered from evidence",
    )


class AISoAJustificationOutput(BaseModel):
    """Structured output for Statement of Applicability inclusion/exclusion justification."""

    control_id: str = Field(description="ISO 27001 Annex A control ID")
    is_applicable: bool = Field(description="Whether control is applicable to organization scope")
    justification: str = Field(description="Formal audit justification for inclusion or exclusion")
    suggested_implementation_status: Literal["Implemented", "In Progress", "Planned", "Not Implemented"]

