# Детальные подзадачи реализации системы KIM

Каждый пункт из `Plan.MD` разбит на конкретные подзадачи с описанием требований.

---

## 1. Инициализация проекта и настройка окружения

### 1.1 Создание структуры директорий
- Создать директорию `src/kim/` для основного пакета
- Создать директорию `tests/` для тестов
- Добавить `__init__.py` в `src/kim/`

### 1.2 Конфигурация `pyproject.toml`
- Указать `name = "kim"`, `version`, описание, `requires-python = ">=3.11"`
- Добавить зависимости: `anthropic>=0.40.0`, `pydantic>=2.0.0`, `rich>=13.0.0`, `typer>=0.12.0`
- Добавить dev-зависимости: `pytest`, `pytest-mock`
- Настроить точку входа CLI: `[project.scripts] kim = "kim.cli:app"`
- Указать `[tool.setuptools.packages.find]` с `where = ["src"]`

### 1.3 Создание `.gitignore`
- Исключить `__pycache__/`, `*.pyc`, `.env`, `*.egg-info/`, `.venv/`, `dist/`

### 1.4 Проверка окружения
- Убедиться, что установка `pip install -e .` проходит без ошибок
- Убедиться, что `pip install -e ".[dev]"` устанавливает dev-зависимости

---

## 2. Разработка моделей данных (Data Models)

**Файл:** `src/kim/models.py`

### 2.1 Перечисление `SocialPolicySector`
- Создать `SocialPolicySector(str, Enum)` с 10 значениями:
  `healthcare`, `education`, `housing`, `employment`, `social_protection`,
  `youth_policy`, `family_policy`, `disability_support`, `elderly_care`, `ecology`
- Наследование от `str` обеспечивает сериализацию в JSON как строки

### 2.2 Словарь русских названий `SECTOR_LABELS_RU`
- Создать `dict[SocialPolicySector, str]` с человекочитаемыми русскими названиями для каждого сектора
- Используется в промптах для агентов

### 2.3 Модель `CityProblem`
- Поля: `city: str`, `sector: SocialPolicySector`, `title: str`, `description: str`
- `severity: int` с валидацией `ge=1, le=10`
- `affected_population: Optional[str] = None`
- `root_causes: List[str] = []`

### 2.4 Модель `LegislativeGap`
- Поля: `sector: SocialPolicySector`, `title: str`, `description: str`
- `existing_norms: List[str] = []`
- `missing_regulation: str`
- `impact: str`

### 2.5 Модель `Initiative`
- Поля: `title: str`, `sector: SocialPolicySector`, `target_cities: List[str] = []`
- `description: str`, `objectives: List[str] = []`
- `implementation_steps: List[str] = []`
- `addresses_problems: List[str] = []`
- `requires_legislation: bool = False`
- `estimated_impact: str`

### 2.6 Модель `AnalysisReport`
- Поля: `city: str`, `sector: SocialPolicySector`
- `problems: List[CityProblem] = []`
- `legislative_gaps: List[LegislativeGap] = []`
- `initiatives: List[Initiative] = []`

---

## 3. Реализация специализированных агентов

**Файл:** `src/kim/agents.py`

### 3.1 Вспомогательная функция `_parse_json_response`
- Принимает строку с ответом LLM
- Удаляет markdown-обёртку ` ```json ... ``` ` если присутствует
- Вызывает `json.loads()` и возвращает распарсенный объект
- Требование: функция должна корректно обрабатывать ответы как с обёрткой, так и без

### 3.2 Функция `_make_client`
- Возвращает `anthropic.Anthropic()` (клиент читает ключ из `ANTHROPIC_API_KEY`)
- Выделена отдельно для удобства мокирования в тестах

### 3.3 Класс `ProblemIdentifierAgent`
- Системный промпт: эксперт по социальной политике России, ответ только JSON
- Метод `run(client, city, sector) -> list[CityProblem]`
- Промпт запрашивает 3-5 проблем с полями: `city`, `sector`, `title`, `description`, `severity`, `affected_population`, `root_causes`
- Логирование через `logger.debug` на входе и при получении ответа (первые 300 символов)
- Десериализация через `[CityProblem(**item) for item in data]`

### 3.4 Класс `LegislativeAnalystAgent`
- Системный промпт: юрист-эксперт по социальному законодательству России, ответ только JSON
- Метод `run(client, sector, problems) -> list[LegislativeGap]`
- Промпт передаёт заголовки проблем через `"; ".join(p.title for p in problems)`
- Запрашивает 2-4 пробела с полями: `sector`, `title`, `description`, `existing_norms`, `missing_regulation`, `impact`
- Логирование аналогично п. 3.3

### 3.5 Класс `InitiativeGeneratorAgent`
- Системный промпт: эксперт по разработке государственных инициатив, ответ только JSON
- Метод `run(client, city, sector, problems, gaps) -> list[Initiative]`
- Промпт передаёт заголовки проблем и пробелов
- Запрашивает 2-3 инициативы с полями: `title`, `sector`, `target_cities`, `description`, `objectives`, `implementation_steps`, `addresses_problems`, `requires_legislation`, `estimated_impact`
- Логирование аналогично п. 3.3

---

## 4. Реализация оркестратора

**Файл:** `src/kim/agents.py` (продолжение)

### 4.1 Класс `OrchestratorAgent`
- Метод `__init__`: создаёт единый `anthropic.Anthropic` клиент и три специализированных агента

### 4.2 Метод `analyze`
- Сигнатура: `analyze(self, city: str, sector: SocialPolicySector, *, on_step: Any = None) -> AnalysisReport`
- Шаг 1: если передан `on_step`, вызвать `on_step("problems")`; запустить `ProblemIdentifierAgent.run()`
- Шаг 2: если передан `on_step`, вызвать `on_step("legislation")`; запустить `LegislativeAnalystAgent.run()`
- Шаг 3: если передан `on_step`, вызвать `on_step("initiatives")`; запустить `InitiativeGeneratorAgent.run()`
- Вернуть `AnalysisReport(city=city, sector=sector, problems=..., legislative_gaps=..., initiatives=...)`
- Требование: `on_step` — необязательный callback для отображения прогресса в CLI

---

## 5. Разработка CLI-интерфейса

**Файл:** `src/kim/cli.py`

### 5.1 Настройка Typer-приложения
- Создать `app = typer.Typer(help="KIM — AI-система анализа социальной политики")`

### 5.2 Команда `list-sectors`
- Декоратор `@app.command()`
- Вывод таблицы через `rich.console.Console` и `rich.table.Table`
- Столбцы: "Код" и "Название"
- Итерация по `SocialPolicySector` с выводом `sector.value` и `SECTOR_LABELS_RU[sector]`

### 5.3 Команда `analyze`
- Аргументы: `city: str`, `sector: SocialPolicySector`
- Опция: `--output-json: Optional[Path] = None` для сохранения результата в файл
- Запуск `OrchestratorAgent().analyze(city, sector, on_step=...)` с отображением прогресса через `rich.progress` или `rich.console`
- Вывод итогового отчёта в консоль: секции "Проблемы", "Пробелы законодательства", "Инициативы"
- Если `--output-json` задан: сохранить `report.model_dump()` в JSON-файл и вывести подтверждение
- Обработка ошибок: если `ANTHROPIC_API_KEY` не задан, вывести понятное сообщение об ошибке и завершить с кодом 1

### 5.4 Точка входа
- В `pyproject.toml`: `[project.scripts] kim = "kim.cli:app"`
- Убедиться, что `kim --help` работает корректно после `pip install -e .`

---

## 6. Написание тестов

**Файлы:** `tests/test_agents.py`, `tests/test_models.py`

### 6.1 Тесты моделей данных (`test_models.py`)

#### 6.1.1 `CityProblem`
- Тест успешного создания с обязательными полями
- Тест валидации: `severity` < 1 и > 10 должны вызывать `ValidationError`
- Тест значений по умолчанию: `root_causes = []`, `affected_population = None`

#### 6.1.2 `LegislativeGap`
- Тест успешного создания с обязательными полями
- Тест значений по умолчанию: `existing_norms = []`

#### 6.1.3 `Initiative`
- Тест успешного создания
- Тест значений по умолчанию: `requires_legislation = False`, все списки пустые

#### 6.1.4 `SocialPolicySector`
- Тест что значения enum соответствуют ожидаемым строкам
- Тест сериализации в JSON-совместимые строки (наследование от `str`)

### 6.2 Тесты агентов (`test_agents.py`)

#### 6.2.1 Подготовка фикстур
- Создать фиктивный JSON-ответ для `ProblemIdentifierAgent` (список из 1-2 объектов)
- Создать фиктивный JSON-ответ для `LegislativeAnalystAgent`
- Создать фиктивный JSON-ответ для `InitiativeGeneratorAgent`

#### 6.2.2 Тест `ProblemIdentifierAgent.run`
- Мокировать `client.messages.create` через `pytest-mock` или `unittest.mock`
- Убедиться что метод возвращает список `CityProblem`
- Убедиться что `client.messages.create` вызван с правильными `model`, `system`, `messages`

#### 6.2.3 Тест `LegislativeAnalystAgent.run`
- Мокировать `client.messages.create`
- Убедиться что метод возвращает список `LegislativeGap`

#### 6.2.4 Тест `InitiativeGeneratorAgent.run`
- Мокировать `client.messages.create`
- Убедиться что метод возвращает список `Initiative`

#### 6.2.5 Тест `OrchestratorAgent.analyze`
- Мокировать все три специализированных агента через `unittest.mock.patch`
- Убедиться что возвращается `AnalysisReport` с корректными полями `city` и `sector`
- Убедиться что `on_step` вызывается 3 раза с аргументами `"problems"`, `"legislation"`, `"initiatives"`

#### 6.2.6 Тест `_parse_json_response`
- Тест с чистым JSON-строкой
- Тест со строкой в markdown-обёртке ` ```json ... ``` `
- Тест с пустым JSON-массивом `[]`

---

## 7. Документация и финальная конфигурация

### 7.1 `README.md`
- Краткое описание системы и её возможностей
- Раздел "Архитектура" с ASCII-диаграммой агентов
- Таблица отраслей социальной политики (код + название)
- Раздел "Установка": `pip install -e .`, требование Python ≥ 3.11, настройка `ANTHROPIC_API_KEY`
- Раздел "Использование CLI": примеры команд `kim analyze` и `kim list-sectors`
- Раздел "Python API": пример использования `OrchestratorAgent`
- Раздел "Разработка": `pip install -e ".[dev]"` и `pytest tests/`

### 7.2 Финальная проверка `pyproject.toml`
- Убедиться что все зависимости с корректными минимальными версиями
- Убедиться что `[project.optional-dependencies] dev` содержит `pytest` и `pytest-mock`
- Убедиться что `[project.scripts]` указывает на `kim.cli:app`

### 7.3 Финальная проверка работоспособности
- Запустить `pytest tests/` — все тесты должны проходить
- Запустить `kim list-sectors` — должна выводиться таблица секторов
- Проверить `kim --help` и `kim analyze --help`
