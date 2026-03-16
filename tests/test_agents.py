"""Tests for AI agents (using mocks to avoid real API calls)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from kim.agents import (
    InitiativeGeneratorAgent,
    LegislativeAnalystAgent,
    OrchestratorAgent,
    ProblemIdentifierAgent,
    _parse_json_response,
)
from kim.models import (
    CityProblem,
    LegislativeGap,
    SocialPolicySector,
)


# ---------------------------------------------------------------------------
# _parse_json_response
# ---------------------------------------------------------------------------


def test_parse_json_response_plain():
    data = [{"key": "value"}]
    result = _parse_json_response(json.dumps(data))
    assert result == data


def test_parse_json_response_with_fences():
    data = [{"key": "value"}]
    text = "```json\n" + json.dumps(data) + "\n```"
    result = _parse_json_response(text)
    assert result == data


def test_parse_json_response_invalid():
    with pytest.raises(json.JSONDecodeError):
        _parse_json_response("not valid json")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_message(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=content)]
    return msg


SAMPLE_PROBLEMS = [
    {
        "city": "Москва",
        "sector": "healthcare",
        "title": "Нехватка врачей",
        "description": "Острый дефицит участковых терапевтов",
        "severity": 8,
        "affected_population": "Пожилые жители",
        "root_causes": ["Низкие зарплаты"],
    }
]

SAMPLE_GAPS = [
    {
        "sector": "healthcare",
        "title": "Нет норм о минимальном числе врачей",
        "description": "Законодательство не устанавливает норматив обеспеченности врачами",
        "existing_norms": ["ФЗ-323"],
        "missing_regulation": "Нормативы обеспеченности на 1000 жителей",
        "impact": "Перегруженность оставшихся специалистов",
    }
]

SAMPLE_INITIATIVES = [
    {
        "title": "Программа «Земский врач»",
        "sector": "healthcare",
        "target_cities": ["Москва"],
        "description": "Привлечение врачей льготами",
        "objectives": ["Увеличить число врачей"],
        "implementation_steps": ["Создать реестр", "Выделить жильё"],
        "addresses_problems": ["Нехватка врачей"],
        "requires_legislation": False,
        "estimated_impact": "Рост числа врачей на 15%",
    }
]


# ---------------------------------------------------------------------------
# ProblemIdentifierAgent
# ---------------------------------------------------------------------------


def test_problem_identifier_agent():
    client = MagicMock()
    client.messages.create.return_value = _make_message(json.dumps(SAMPLE_PROBLEMS))

    agent = ProblemIdentifierAgent()
    problems = agent.run(client, "Москва", SocialPolicySector.HEALTHCARE)

    assert len(problems) == 1
    assert isinstance(problems[0], CityProblem)
    assert problems[0].title == "Нехватка врачей"
    assert problems[0].severity == 8


# ---------------------------------------------------------------------------
# LegislativeAnalystAgent
# ---------------------------------------------------------------------------


def test_legislative_analyst_agent():
    client = MagicMock()
    client.messages.create.return_value = _make_message(json.dumps(SAMPLE_GAPS))

    problems = [CityProblem(**SAMPLE_PROBLEMS[0])]
    agent = LegislativeAnalystAgent()
    gaps = agent.run(client, SocialPolicySector.HEALTHCARE, problems)

    assert len(gaps) == 1
    assert isinstance(gaps[0], LegislativeGap)
    assert "норм" in gaps[0].title.lower() or gaps[0].title


# ---------------------------------------------------------------------------
# InitiativeGeneratorAgent
# ---------------------------------------------------------------------------


def test_initiative_generator_agent():
    client = MagicMock()
    client.messages.create.return_value = _make_message(json.dumps(SAMPLE_INITIATIVES))

    problems = [CityProblem(**SAMPLE_PROBLEMS[0])]
    gaps = [LegislativeGap(**SAMPLE_GAPS[0])]
    agent = InitiativeGeneratorAgent()
    initiatives = agent.run(client, "Москва", SocialPolicySector.HEALTHCARE, problems, gaps)

    assert len(initiatives) == 1
    assert initiatives[0].title == "Программа «Земский врач»"
    assert initiatives[0].requires_legislation is False


# ---------------------------------------------------------------------------
# OrchestratorAgent
# ---------------------------------------------------------------------------


@patch("kim.agents._make_client")
def test_orchestrator_agent(mock_make_client):
    mock_client = MagicMock()
    mock_make_client.return_value = mock_client

    # Set up return values for each API call in order
    mock_client.messages.create.side_effect = [
        _make_message(json.dumps(SAMPLE_PROBLEMS)),
        _make_message(json.dumps(SAMPLE_GAPS)),
        _make_message(json.dumps(SAMPLE_INITIATIVES)),
    ]

    steps = []
    agent = OrchestratorAgent()
    report = agent.analyze("Москва", SocialPolicySector.HEALTHCARE, on_step=steps.append)

    assert report.city == "Москва"
    assert report.sector == SocialPolicySector.HEALTHCARE
    assert len(report.problems) == 1
    assert len(report.legislative_gaps) == 1
    assert len(report.initiatives) == 1
    assert steps == ["problems", "legislation", "initiatives"]
