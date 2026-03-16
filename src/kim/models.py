"""Core data models for the social policy analysis system."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SocialPolicySector(str, Enum):
    """Sectors of social policy."""

    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    HOUSING = "housing"
    EMPLOYMENT = "employment"
    SOCIAL_PROTECTION = "social_protection"
    YOUTH_POLICY = "youth_policy"
    FAMILY_POLICY = "family_policy"
    DISABILITY_SUPPORT = "disability_support"
    ELDERLY_CARE = "elderly_care"
    ECOLOGY = "ecology"


SECTOR_LABELS_RU: dict[SocialPolicySector, str] = {
    SocialPolicySector.HEALTHCARE: "Здравоохранение",
    SocialPolicySector.EDUCATION: "Образование",
    SocialPolicySector.HOUSING: "Жильё и ЖКХ",
    SocialPolicySector.EMPLOYMENT: "Занятость и рынок труда",
    SocialPolicySector.SOCIAL_PROTECTION: "Социальная защита",
    SocialPolicySector.YOUTH_POLICY: "Молодёжная политика",
    SocialPolicySector.FAMILY_POLICY: "Семейная политика",
    SocialPolicySector.DISABILITY_SUPPORT: "Поддержка людей с инвалидностью",
    SocialPolicySector.ELDERLY_CARE: "Забота о пожилых",
    SocialPolicySector.ECOLOGY: "Экология и городская среда",
}


class CityProblem(BaseModel):
    """A key social problem identified for a specific city."""

    city: str = Field(..., description="City name")
    sector: SocialPolicySector = Field(..., description="Social policy sector")
    title: str = Field(..., description="Short title of the problem")
    description: str = Field(..., description="Detailed description")
    severity: int = Field(..., ge=1, le=10, description="Severity score 1-10")
    affected_population: Optional[str] = Field(
        None, description="Groups of people affected"
    )
    root_causes: List[str] = Field(default_factory=list, description="Root causes")


class LegislativeGap(BaseModel):
    """A gap or deficiency identified in legislation."""

    sector: SocialPolicySector = Field(..., description="Social policy sector")
    title: str = Field(..., description="Short title of the gap")
    description: str = Field(..., description="Description of the legislative gap")
    existing_norms: List[str] = Field(
        default_factory=list, description="Existing legal norms"
    )
    missing_regulation: str = Field(
        ..., description="What regulation is missing or insufficient"
    )
    impact: str = Field(..., description="Impact of this gap on citizens")


class Initiative(BaseModel):
    """A generated policy initiative proposal."""

    title: str = Field(..., description="Title of the initiative")
    sector: SocialPolicySector = Field(..., description="Social policy sector")
    target_cities: List[str] = Field(
        default_factory=list, description="Cities this addresses"
    )
    description: str = Field(..., description="Full description of the initiative")
    objectives: List[str] = Field(default_factory=list, description="Key objectives")
    implementation_steps: List[str] = Field(
        default_factory=list, description="Steps to implement"
    )
    addresses_problems: List[str] = Field(
        default_factory=list, description="Problems this initiative addresses"
    )
    requires_legislation: bool = Field(
        False, description="Whether legislative changes are needed"
    )
    estimated_impact: str = Field(..., description="Expected impact")


class AnalysisReport(BaseModel):
    """Full analysis report for a city and sector."""

    city: str
    sector: SocialPolicySector
    problems: List[CityProblem] = Field(default_factory=list)
    legislative_gaps: List[LegislativeGap] = Field(default_factory=list)
    initiatives: List[Initiative] = Field(default_factory=list)
