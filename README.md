# KIM — AI-powered Social Policy Analysis System

**KIM** — система анализа социальной политики на основе ИИ-агентов.

Система позволяет:
- 🔍 **Выявлять ключевые проблемы** по городам и отраслям социальной политики
- ⚖️ **Анализировать пробелы законодательства**, препятствующие решению этих проблем
- 💡 **Генерировать идеи инициатив** для устранения выявленных проблем

## Архитектура

```
OrchestratorAgent
├── ProblemIdentifierAgent   — выявление проблем города/отрасли
├── LegislativeAnalystAgent  — анализ пробелов законодательства
└── InitiativeGeneratorAgent — генерация инициатив
```

Каждый агент использует Claude (Anthropic) через официальный Python SDK.

## Отрасли социальной политики

| Код | Название |
|-----|----------|
| `healthcare` | Здравоохранение |
| `education` | Образование |
| `housing` | Жильё и ЖКХ |
| `employment` | Занятость и рынок труда |
| `social_protection` | Социальная защита |
| `youth_policy` | Молодёжная политика |
| `family_policy` | Семейная политика |
| `disability_support` | Поддержка людей с инвалидностью |
| `elderly_care` | Забота о пожилых |
| `ecology` | Экология и городская среда |

## Установка

```bash
pip install -e .
```

Требуется Python ≥ 3.11 и ключ Anthropic API:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Использование

### CLI

```bash
# Анализ конкретного города и отрасли
kim analyze Москва healthcare

# Сохранить результат в JSON
kim analyze "Нижний Новгород" education --output-json report.json

# Список доступных отраслей
kim list-sectors
```

### Python API

```python
from kim.agents import OrchestratorAgent
from kim.models import SocialPolicySector

agent = OrchestratorAgent()
report = agent.analyze("Казань", SocialPolicySector.HOUSING)

for problem in report.problems:
    print(f"{problem.title} (серьёзность: {problem.severity}/10)")

for initiative in report.initiatives:
    print(f"Инициатива: {initiative.title}")
```

## Разработка

```bash
pip install -e ".[dev]"
pytest tests/
```
