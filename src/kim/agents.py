"""AI agents for the social policy analysis system.

Each agent is responsible for a specific analytical task:
- ProblemIdentifierAgent: identifies key social problems in a city/sector
- LegislativeAnalystAgent: detects gaps in legislation
- InitiativeGeneratorAgent: generates policy initiative ideas
- OrchestratorAgent: coordinates all agents and produces the final report
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from kim.models import (
    AnalysisReport,
    CityProblem,
    Initiative,
    LegislativeGap,
    SECTOR_LABELS_RU,
    SocialPolicySector,
)

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_json_response(text: str) -> Any:
    """Extract and parse the first JSON object/array found in an LLM response."""
    # Strip markdown code fences if present
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # Drop first and last lines (the fence lines)
        inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        stripped = inner.strip()
    return json.loads(stripped)


def _make_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Problem Identifier Agent
# ---------------------------------------------------------------------------


class ProblemIdentifierAgent:
    """Identifies key social problems for a given city and sector."""

    SYSTEM_PROMPT = (
        "Ты эксперт по социальной политике в России. "
        "Твоя задача — выявлять ключевые социальные проблемы в конкретном городе "
        "в рамках указанной отрасли социальной политики. "
        "Отвечай ТОЛЬКО валидным JSON-массивом объектов без дополнительного текста."
    )

    def run(
        self,
        client: anthropic.Anthropic,
        city: str,
        sector: SocialPolicySector,
    ) -> list[CityProblem]:
        sector_label = SECTOR_LABELS_RU[sector]
        user_message = (
            f"Выяви 3-5 ключевых социальных проблем в городе «{city}» "
            f"в отрасли «{sector_label}». "
            "Верни JSON-массив объектов со следующими полями:\n"
            "- city (string)\n"
            "- sector (string, значение из списка: "
            + ", ".join(s.value for s in SocialPolicySector)
            + ")\n"
            "- title (string)\n"
            "- description (string)\n"
            "- severity (integer 1-10)\n"
            "- affected_population (string)\n"
            "- root_causes (array of strings)"
        )

        logger.debug("ProblemIdentifierAgent: calling Claude for city=%s sector=%s", city, sector)
        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text
        logger.debug("ProblemIdentifierAgent raw response: %s", raw[:300])
        data = _parse_json_response(raw)
        return [CityProblem(**item) for item in data]


# ---------------------------------------------------------------------------
# Legislative Analyst Agent
# ---------------------------------------------------------------------------


class LegislativeAnalystAgent:
    """Detects gaps and deficiencies in legislation for a given sector."""

    SYSTEM_PROMPT = (
        "Ты юрист-эксперт по социальному законодательству России. "
        "Твоя задача — выявлять пробелы и недостатки действующего законодательства "
        "в конкретной отрасли социальной политики. "
        "Отвечай ТОЛЬКО валидным JSON-массивом объектов без дополнительного текста."
    )

    def run(
        self,
        client: anthropic.Anthropic,
        sector: SocialPolicySector,
        problems: list[CityProblem],
    ) -> list[LegislativeGap]:
        sector_label = SECTOR_LABELS_RU[sector]
        problem_titles = "; ".join(p.title for p in problems)
        user_message = (
            f"В отрасли «{sector_label}» выявлены следующие проблемы: {problem_titles}. "
            "Определи 2-4 ключевых пробела в действующем законодательстве, "
            "которые способствуют этим проблемам. "
            "Верни JSON-массив объектов со следующими полями:\n"
            "- sector (string, значение: " + sector.value + ")\n"
            "- title (string)\n"
            "- description (string)\n"
            "- existing_norms (array of strings)\n"
            "- missing_regulation (string)\n"
            "- impact (string)"
        )

        logger.debug("LegislativeAnalystAgent: calling Claude for sector=%s", sector)
        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text
        logger.debug("LegislativeAnalystAgent raw response: %s", raw[:300])
        data = _parse_json_response(raw)
        return [LegislativeGap(**item) for item in data]


# ---------------------------------------------------------------------------
# Initiative Generator Agent
# ---------------------------------------------------------------------------


class InitiativeGeneratorAgent:
    """Generates policy initiative proposals based on identified problems and gaps."""

    SYSTEM_PROMPT = (
        "Ты эксперт по разработке государственных инициатив в области социальной политики. "
        "Твоя задача — генерировать конкретные, реализуемые инициативы "
        "для решения выявленных проблем и устранения пробелов законодательства. "
        "Отвечай ТОЛЬКО валидным JSON-массивом объектов без дополнительного текста."
    )

    def run(
        self,
        client: anthropic.Anthropic,
        city: str,
        sector: SocialPolicySector,
        problems: list[CityProblem],
        gaps: list[LegislativeGap],
    ) -> list[Initiative]:
        sector_label = SECTOR_LABELS_RU[sector]
        problem_titles = "; ".join(p.title for p in problems)
        gap_titles = "; ".join(g.title for g in gaps)
        user_message = (
            f"Для города «{city}» в отрасли «{sector_label}» выявлены проблемы: {problem_titles}. "
            f"Пробелы законодательства: {gap_titles}. "
            "Сгенерируй 2-3 конкретные инициативы для их решения. "
            "Верни JSON-массив объектов со следующими полями:\n"
            "- title (string)\n"
            "- sector (string, значение: " + sector.value + ")\n"
            "- target_cities (array of strings)\n"
            "- description (string)\n"
            "- objectives (array of strings)\n"
            "- implementation_steps (array of strings)\n"
            "- addresses_problems (array of strings)\n"
            "- requires_legislation (boolean)\n"
            "- estimated_impact (string)"
        )

        logger.debug("InitiativeGeneratorAgent: calling Claude for city=%s sector=%s", city, sector)
        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text
        logger.debug("InitiativeGeneratorAgent raw response: %s", raw[:300])
        data = _parse_json_response(raw)
        return [Initiative(**item) for item in data]


# ---------------------------------------------------------------------------
# Orchestrator Agent
# ---------------------------------------------------------------------------


class OrchestratorAgent:
    """Coordinates all specialist agents to produce a full AnalysisReport."""

    def __init__(self) -> None:
        self._client = _make_client()
        self._problem_agent = ProblemIdentifierAgent()
        self._legislative_agent = LegislativeAnalystAgent()
        self._initiative_agent = InitiativeGeneratorAgent()

    def analyze(
        self,
        city: str,
        sector: SocialPolicySector,
        *,
        on_step: Any = None,
    ) -> AnalysisReport:
        """Run a full analysis pipeline for a city and sector.

        Args:
            city: City name.
            sector: Social policy sector.
            on_step: Optional callback(step_name: str) called before each agent step.

        Returns:
            A fully populated AnalysisReport.
        """
        if on_step:
            on_step("problems")
        problems = self._problem_agent.run(self._client, city, sector)

        if on_step:
            on_step("legislation")
        gaps = self._legislative_agent.run(self._client, sector, problems)

        if on_step:
            on_step("initiatives")
        initiatives = self._initiative_agent.run(
            self._client, city, sector, problems, gaps
        )

        return AnalysisReport(
            city=city,
            sector=sector,
            problems=problems,
            legislative_gaps=gaps,
            initiatives=initiatives,
        )
