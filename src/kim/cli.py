"""CLI interface for the KIM social policy analysis system."""

from __future__ import annotations

import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

from kim.models import AnalysisReport, SECTOR_LABELS_RU, SocialPolicySector

app = typer.Typer(
    name="kim",
    help="KIM — AI-powered social policy analysis system.",
    add_completion=False,
)
console = Console()

STEP_LABELS = {
    "problems": "Выявление ключевых проблем...",
    "legislation": "Анализ законодательства...",
    "initiatives": "Генерация инициатив...",
}


def _sector_choices() -> str:
    return ", ".join(
        f"{s.value} ({SECTOR_LABELS_RU[s]})" for s in SocialPolicySector
    )


def _print_report(report: AnalysisReport) -> None:
    sector_label = SECTOR_LABELS_RU[report.sector]
    console.print()
    console.print(
        Panel(
            f"[bold cyan]Анализ: {report.city} / {sector_label}[/bold cyan]",
            expand=False,
        )
    )

    # ── Problems ──────────────────────────────────────────────────────────
    if report.problems:
        console.print("\n[bold yellow]🔍 Ключевые проблемы[/bold yellow]")
        for i, p in enumerate(report.problems, 1):
            console.print(f"\n  [bold]{i}. {p.title}[/bold]  [red](серьёзность: {p.severity}/10)[/red]")
            console.print(f"     {p.description}")
            if p.affected_population:
                console.print(f"     👥 Затронутые группы: {p.affected_population}")
            if p.root_causes:
                console.print("     📌 Причины: " + "; ".join(p.root_causes))

    # ── Legislative gaps ──────────────────────────────────────────────────
    if report.legislative_gaps:
        console.print("\n[bold magenta]⚖️  Пробелы законодательства[/bold magenta]")
        for i, g in enumerate(report.legislative_gaps, 1):
            console.print(f"\n  [bold]{i}. {g.title}[/bold]")
            console.print(f"     {g.description}")
            console.print(f"     🚫 Чего не хватает: {g.missing_regulation}")
            console.print(f"     💥 Последствия: {g.impact}")

    # ── Initiatives ───────────────────────────────────────────────────────
    if report.initiatives:
        console.print("\n[bold green]💡 Предлагаемые инициативы[/bold green]")
        for i, init in enumerate(report.initiatives, 1):
            leg = " [yellow](требует изменений в законодательстве)[/yellow]" if init.requires_legislation else ""
            console.print(f"\n  [bold]{i}. {init.title}[/bold]{leg}")
            console.print(f"     {init.description}")
            if init.objectives:
                console.print("     🎯 Цели: " + "; ".join(init.objectives))
            if init.implementation_steps:
                console.print("     📋 Шаги реализации:")
                for step in init.implementation_steps:
                    console.print(f"        • {step}")
            console.print(f"     📈 Ожидаемый эффект: {init.estimated_impact}")

    console.print()


@app.command()
def analyze(
    city: str = typer.Argument(..., help="Название города для анализа"),
    sector: str = typer.Argument(
        ...,
        help=f"Отрасль социальной политики. Доступные значения: {', '.join(s.value for s in SocialPolicySector)}",
    ),
    output_json: Optional[str] = typer.Option(
        None,
        "--output-json",
        "-o",
        help="Сохранить результат в JSON-файл",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
) -> None:
    """Провести анализ социальных проблем города в выбранной отрасли."""
    import logging

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Validate sector
    try:
        sector_enum = SocialPolicySector(sector)
    except ValueError:
        console.print(
            f"[red]Ошибка:[/red] неизвестная отрасль '{sector}'.\n"
            f"Доступные значения: {_sector_choices()}"
        )
        raise typer.Exit(1)

    # Import here to avoid slow import on --help
    from kim.agents import OrchestratorAgent

    agent = OrchestratorAgent()
    report: Optional[AnalysisReport] = None
    current_step_label = ""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Запуск анализа...", total=None)

        def on_step(step_name: str) -> None:
            nonlocal current_step_label
            current_step_label = STEP_LABELS.get(step_name, step_name)
            progress.update(task, description=current_step_label)

        try:
            report = agent.analyze(city, sector_enum, on_step=on_step)
        except Exception as exc:
            console.print(f"[red]Ошибка при анализе:[/red] {exc}")
            raise typer.Exit(1)

    _print_report(report)

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)
        console.print(f"[dim]Результат сохранён в {output_json}[/dim]")


@app.command("list-sectors")
def list_sectors() -> None:
    """Вывести список доступных отраслей социальной политики."""
    table = Table(title="Отрасли социальной политики", show_lines=True)
    table.add_column("Код", style="cyan", no_wrap=True)
    table.add_column("Название", style="white")
    for sector in SocialPolicySector:
        table.add_row(sector.value, SECTOR_LABELS_RU[sector])
    console.print(table)


if __name__ == "__main__":
    app()
