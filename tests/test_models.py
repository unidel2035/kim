"""Tests for core data models."""

import pytest
from pydantic import ValidationError

from kim.models import (
    AnalysisReport,
    CityProblem,
    Initiative,
    LegislativeGap,
    SECTOR_LABELS_RU,
    SocialPolicySector,
)


def test_all_sectors_have_labels():
    for sector in SocialPolicySector:
        assert sector in SECTOR_LABELS_RU
        assert len(SECTOR_LABELS_RU[sector]) > 0


def test_city_problem_valid():
    problem = CityProblem(
        city="Москва",
        sector=SocialPolicySector.HEALTHCARE,
        title="Нехватка врачей",
        description="Острый дефицит участковых терапевтов",
        severity=8,
        affected_population="Пожилые жители",
        root_causes=["Низкие зарплаты", "Отток кадров"],
    )
    assert problem.city == "Москва"
    assert problem.severity == 8


def test_city_problem_severity_bounds():
    with pytest.raises(ValidationError):
        CityProblem(
            city="Москва",
            sector=SocialPolicySector.HEALTHCARE,
            title="Test",
            description="Test",
            severity=11,  # out of range
        )
    with pytest.raises(ValidationError):
        CityProblem(
            city="Москва",
            sector=SocialPolicySector.HEALTHCARE,
            title="Test",
            description="Test",
            severity=0,  # out of range
        )


def test_legislative_gap_valid():
    gap = LegislativeGap(
        sector=SocialPolicySector.EDUCATION,
        title="Отсутствие норм инклюзии",
        description="Недостаточное регулирование инклюзивного образования",
        existing_norms=["ФЗ-273"],
        missing_regulation="Норм об адаптированных программах",
        impact="Дети с ОВЗ не получают необходимой поддержки",
    )
    assert gap.sector == SocialPolicySector.EDUCATION


def test_initiative_valid():
    initiative = Initiative(
        title="Программа поддержки молодых врачей",
        sector=SocialPolicySector.HEALTHCARE,
        target_cities=["Москва", "СПб"],
        description="Комплексная программа привлечения молодых врачей",
        objectives=["Увеличить число врачей на 20%"],
        implementation_steps=["Создать реестр вакансий", "Запустить льготы"],
        addresses_problems=["Нехватка врачей"],
        requires_legislation=True,
        estimated_impact="Сокращение очередей на 30%",
    )
    assert initiative.requires_legislation is True


def test_analysis_report_aggregates():
    report = AnalysisReport(
        city="Казань",
        sector=SocialPolicySector.HOUSING,
    )
    assert report.problems == []
    assert report.legislative_gaps == []
    assert report.initiatives == []
