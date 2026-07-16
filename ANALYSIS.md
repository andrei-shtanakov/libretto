# Libretto — Полное исследование

> Язык программирования для AI-сессий. 90 файлов, 896KB, 0 runtime-зависимостей.

> **Обновление 2026-07-16.** Статус репозитория: активный downstream / research
> fork апстрима [`openprose/prose`](https://github.com/openprose/prose)
> (апстрим ушёл в responsibility-модель + TypeScript Reactor runtime; этот репо
> сохраняет spec-as-VM `.libretto` и перенимает протоколы — receipts, compile IR,
> materiality — на Python-тулинге). Семифазная эмпирическая оценка
> (`evaluation/results/final-verdict.md`) подтвердила faithful-исполнение всего
> языка при **2–6× token premium**; ~51% затрат представительного запуска —
> оверхед границ сессий (~46K токенов floor на сессию). Вывод: инструмент
> надёжности/аудируемости, не эффективности. План развития:
> `docs/plans/2026-07-16-development-plan.md`.

---

## 1.1. Назначение и роль в экосистеме

- **Тип**: оркестрация (pure — без собственного runtime)
- **Основные задачи**:
  - Декларативное описание multi-agent workflows в `.libretto` файлах
  - Исполнение через "simulation is execution" — LLM читает spec VM и *становится* VM
  - Персистентная память агентов, state management, рекурсивная композиция программ
- **Пользователи**: разработчики, работающие с Claude Code / OpenCode / Amp. Любой AI harness с поддержкой subagent spawn считается "Prose Complete"

## 1.2. Контекст

- **Происхождение**: extensions/libretto внутри проекта openclaw (AI gateway)
- **Связь с openclaw**: минимальная (5-строчный no-op index.ts + plugin manifest). Core openclaw не зависит от libretto, libretto не зависит от core openclaw
- **Внешние зависимости**: **ноль**. Никаких npm/pip/cargo. Только markdown-файлы, читаемые LLM
- **Лицензия**: MIT

---

## 2. Архитектура

### 2.1. Высокоуровневая схема

- **Архстиль**: "specification-as-VM" — спецификация описывает виртуальную машину, LLM симулирует её, симуляция с достаточной точностью *является* реализацией
- **Основные компоненты**:
  - `libretto.md` (36KB) — execution semantics, VM specification
  - `compiler.md` (83KB, 2971 строк) — full grammar, validation rules, compilation
  - `state/` (4 backends) — filesystem, in-context, sqlite, postgres
  - `primitives/session.md` — subagent context management, compaction guidelines
  - `guidance/` — patterns, antipatterns, system-prompt enforcement
  - `lib/` (9 .libretto programs) — stdlib: inspector, profiler, cost-analyzer, memory и др.
  - `examples/` (51 .libretto programs) — от hello-world до "построй браузер"
  - `alts/` (5 альтернативных синтаксисов) — Borges, Folk, Arabian Nights, Homer, Kafka
- **Входы/Выходы**: `.libretto` файл → VM (LLM) → Task tool calls → субагенты → артефакты + state

### 2.2. Слои и границы

| Слой | Что содержит | Формат |
|------|-------------|--------|
| **Language spec** | Грамматика, семантика | `compiler.md` |
| **VM runtime** | Execution model, spawning, state | `libretto.md` |
| **State backends** | 4 стратегии персистентности | `state/*.md` |
| **Session primitives** | Контекст, компактификация, output writing | `primitives/session.md` |
| **Guidance** | Паттерны, антипаттерны, enforcement | `guidance/*.md` |
| **Stdlib** | Meta-tools: inspect, profile, improve | `lib/*.libretto` |
| **Examples** | 51 программа-образец | `examples/*.libretto` |
| **Syntax skins** | 5 альтернативных регистров | `alts/*.md` |

### 2.3. Хранение состояния

| Backend | Где хранится | Concurrent writes | Resumability | Зависимости |
|---------|-------------|-------------------|-------------|-------------|
| **filesystem** (default) | `.libretto/runs/{id}/` | Нет (single VM) | Да, через `state.md` | Нет |
| **in-context** | Conversation history | Нет | Нет (ephemeral) | Нет |
| **sqlite** | `.libretto/runs/{id}/state.db` | Ограничено (table locks) | Да, atomic | `sqlite3` CLI |
| **postgres** | PostgreSQL database | Да (row-level locks) | Да | `psql` + PostgreSQL server |

**Модель консистентности**: VM — единственный writer для `state.md`. Субагенты пишут свои bindings и agent memory. VM *никогда* не держит полные значения — только указатели (pointer-based context passing).

---

## 3. Оркестрация агентов

### 3.1. Модель оркестрации

- **Типы агентов**: определяются пользователем через `agent name:` с model, prompt, persist
- **Роли (типичные паттерны)**: captain/coordinator, researcher, coder, critic, tester — но не зашиты в язык
- **Схема взаимодействия**: чистый оркестратор (VM управляет всеми сессиями)
- **Поддерживаемые паттерны**:
  - Последовательность (statement за statement)
  - Параллелизм (`parallel:` с стратегиями all/first/any/any+count)
  - Ветвления (`if **condition**:`, `choice **criteria**:`)
  - Циклы (`loop until`, `repeat N`, `for...in`, `parallel for`)
  - Рекурсия (блоки могут вызывать себя, max depth 100)
  - Retry с backoff (`retry: N`, `backoff: exponential`)
  - Try/catch/finally
  - Pipelines (`| map:`, `| filter:`, `| reduce:`, `| pmap:`)

### 3.2. Планирование и управление задачами

- **Формат задания**: `.libretto` файл — Python-like indentation syntax, self-evident by design
- **Исполнение**: sequential top-to-bottom с explicit control flow
- **Чекпоинты**: `state.md` (filesystem) или narration markers (in-context) обновляются после каждого statement
- **Откаты**: `try/catch` для error recovery. Resumption через чтение `state.md`
- **Идемпотентность**: NDI (Nondeterministic Idempotence) — путь нередетерминирован, но outcome гарантирован при resume

### 3.3. Масштабирование и надёжность

- **Масштабирование**: через `parallel:` блоки. `parallel for` для fan-out. Стратегия `any, count: N` для work-stealing
- **Обработка ошибок**:
  - `retry: N` + `backoff: none/linear/exponential` на уровне session
  - `try/catch/finally` для structured error handling
  - `on-fail: fail-fast/continue/ignore` для parallel блоков
  - `throw` для явного проброса ошибок
  - Паттерн circuit-breaker (в guidance/patterns.md)
- **Ограничения**:
  - `max:` на каждом loop (обязательный best practice)
  - Recursion depth limit: 100 (configurable per-block)
  - No built-in concurrency limit (зависит от substrate)

---

## 4. Мониторинг и контроль

### 4.1. Наблюдаемость

| Сигнал | Уровень | Реализация |
|--------|---------|-----------|
| **Execution trace** | Программа | `state.md` — annotated source code с позицией и статусами |
| **Bindings** | Statement | `bindings/{name}.md` — полный output каждой сессии |
| **Agent memory** | Агент | `agents/{name}/memory.md` + segments `{name}-NNN.md` |
| **Narration markers** | Statement (in-context) | `[Position]`, `[Binding]`, `[Parallel]`, `[Loop]`, `[Try]`, `[Frame+/-]` |
| **Run correlation** | Запуск | Run ID `{YYYYMMDD}-{HHMMSS}-{random6}` |

**Корреляция**: execution_id для block invocations, scoped bindings `{name}__{execution_id}.md`

### 4.2. Инструменты наблюдения (stdlib)

| Инструмент | Назначение | Input | Output |
|-----------|-----------|-------|--------|
| `inspector.libretto` | Post-run evaluation | run path, depth, target | verdicts, scores, diagrams |
| `profiler.libretto` | Performance analysis | run path | cost, time, tokens, cache efficiency |
| `cost-analyzer.libretto` | Cost patterns | run path, scope | hotspots, trends, optimization tips |
| `calibrator.libretto` | Evaluation reliability | run paths, sample | agreement rates, confidence |
| `error-forensics.libretto` | Root cause analysis | run path, focus | classification, chain, fixes |

### 4.3. Управление и аудит

- **Runtime actions**: resume (через `state.md`), нет встроенного pause/cancel (зависит от substrate)
- **Аудит**: полный — `state.md` содержит annotated trace, `bindings/` содержат все промежуточные значения, `agents/` содержат все segment records
- **Drill-down**: от program → statement → binding → agent segment

---

## 5. Спеки, конфигурация и расширяемость

### 5.1. Спецификации задач/флоу

- **Формат**: `.libretto` — Python-like indentation, markdown-friendly
- **Исполняемость**: полностью исполняемый — VM парсит и выполняет
- **Грамматика**: формально специфицирована в `compiler.md` (2971 строк, BNF-style)
- **Версионирование**: нет встроенного. Файлы — обычные текстовые, хранятся в git

### 5.2. Конфигурация агентов и политик

- **Агенты**: `agent name:` с model, prompt, persist, permissions, skills, retry, backoff
- **Permissions**: `permissions:` блок с read/write/bash allow/deny (enforcement через substrate)
- **Хранение конфигов**: inline в `.libretto` файле. `.libretto/.env` для runtime config (key=value)
- **Разделение**: agents определяются в программе, runtime state в `.libretto/runs/`

### 5.3. Расширяемость

| Механизм | Что расширяет | Как |
|----------|-------------|-----|
| `use "handle/slug"` | Импорт программ из реестра `p.libretto.md` | Fetch + parse + execute |
| `agent name:` | Новые типы агентов | Inline definition |
| `block name():` | Reusable workflows | Parameterized procedures |
| `alts/*.md` | Синтаксические скины | Keyword translation map |
| `state/*.md` | State backends | New backend = new .md spec |
| `lib/*.libretto` | Meta-tools | Self-contained .libretto programs |

**Что зашито жёстко**: базовые конструкты языка (session, parallel, loop, if, try). Всё остальное расширяемо.

---

## 6. Качество и эксплуатация

### 6.1. Тестирование

- **Отсутствует формальное тестирование** — нет unit tests, нет CI. Это spec-first система: "тестирование" = компиляция .libretto файлов через `libretto compile`
- **Compiler (`libretto compile`)**: валидирует syntax correctness, semantic validity, self-evidence
- **Inspector (lib/inspector.libretto)**: post-run evaluation, quasi-тестирование через анализ запусков
- **Calibrator**: meta-тестирование — насколько light evaluation надёжна vs deep
- **51 пример** как implicit test suite — если VM может их интерпретировать, spec работает

### 6.2. Performance и масштаб

- **Bottlenecks**: каждый `session` = отдельный API call. Gas Town (пример 28) с 30 polecats = сотни вызовов
- **Стратегии оптимизации**:
  - Model tiering: sonnet для orchestration, opus для hard work, haiku sparingly
  - Context minimization: pointer-based passing, не value-based
  - Batch similar work: один session вместо many
  - Early termination: exit loops ASAP
  - Progressive disclosure: cheap checks first, expensive only if needed
- **Backpressure**: нет встроенного. `max:` на loops — единственная защита от штормов

### 6.3. Операционные практики

- **CI/CD**: отсутствует (pure specification)
- **Миграции**: `libretto update` конвертирует legacy format (state.json → .env, execution/ → runs/)
- **Impact analysis**: любое изменение в `libretto.md` или `compiler.md` потенциально влияет на ВСЕ .libretto программы

---

## 7. Уникальные концепции

### 7.1. "Simulation is Execution"

Центральная идея: LLM — это универсальный симулятор. Если дать ему достаточно детальное описание VM (libretto.md = 36KB), он начинает её симулировать. Но когда симуляция порождает реальные субагенты (Task tool), реальные файлы, реальное состояние — различие между "симулирует VM" и "является VM" исчезает.

### 7.2. Discretion (`**...**`)

"Четвёртая стена" — место где структура уступает AI-суждению:
```prose
loop until **the code is production-ready**:
choice **the appropriate severity level**:
if **the review found critical security issues**:
```
Это не boolean expressions — это natural language conditions, evaluated by the VM's intelligence. Triple asterisks `***...***` для multi-line conditions.

### 7.3. Pointer-based Context

VM никогда не держит полные значения bindings. Только указатели:
```
Binding written: research
Location: .libretto/runs/20260115-143052-a7b3c9/bindings/research.md
Summary: AI safety research covering alignment, robustness...
```
Это позволяет arbitrarily large intermediate values без раздувания контекста VM.

### 7.4. Self-Improvement Loop

```
Run Program → Inspector → VM Improver → PR (улучшает VM)
                       → Program Improver → PR (улучшает .libretto)
                       → Cost Analyzer → оптимизации
                       → Calibrator → reliability check
```
Система способна анализировать и улучшать саму себя.

### 7.5. Persistent Agents с Compaction

Агенты с `persist: true/project/user` накапливают знания:
- `memory.md` — текущее понимание (compacted, не summarized)
- `{name}-NNN.md` — исторические сегменты
- Compaction guidelines: preserve specifics (file:line), decisions with rationale, open concerns. Drop reasoning chains, false starts, verbose quotes.
- 3 уровня scope: execution (dies with run), project (survives runs), user (cross-project)

### 7.6. Alternative Syntax Registers

Один и тот же язык в 6 "одеждах":

| Register | agent | session | parallel | loop | const |
|----------|-------|---------|----------|------|-------|
| Functional | agent | session | parallel | loop | const |
| Borges | dreamer | dream | forking | labyrinth | zahir |
| Folk | sprite | scene | ensemble | — | — |
| Arabian Nights | djinn | tale | bazaar | telling | oath |
| Homer | hero | trial | host | — | — |
| Kafka | clerk | proceeding | departments | appeal | — |

Не декорация — benchmark для исследования learnability и memorability разных метафор.

---

## 8. Количественный профиль

| Метрика | Значение |
|---------|---------|
| Файлов всего | 90 |
| .libretto файлов | 64 (51 examples + 9 lib + 4 roadmap) |
| .md файлов | 25 (specs + guidance + alts + README + ROADMAP) |
| Общий размер | 896 KB |
| VM spec (libretto.md) | 36 KB, 1237 строк |
| Compiler spec | 83 KB, 2971 строк |
| Examples | 51 программа |
| Stdlib programs | 9 |
| State backends | 4 |
| Syntax registers | 6 (functional + 5 alts) |
| Runtime зависимости | 0 |
| Строк TypeScript | 5 (no-op wrapper, удалён при выделении) |
| License | MIT |

---

## 9. Сравнение с аналогами

| | Libretto | LangChain/LangGraph | AutoGen | CrewAI |
|---|---|---|---|---|
| **Подход** | Spec → LLM simulates VM | Python library | Python framework | Python framework |
| **Runtime** | Любой "Prose Complete" LLM | Python process | Python process | Python process |
| **Зависимости** | 0 | pip install (heavy) | pip install | pip install |
| **Портируемость** | Claude Code, OpenCode, Amp | Привязан к LangChain | Привязан к AutoGen | Привязан к CrewAI |
| **State** | 4 backends (file/ctx/sqlite/pg) | Custom / LangGraph checkpoints | Custom | Custom |
| **Persistent agents** | Built-in (3 scopes) | Через LangGraph state | Через custom code | Нет |
| **Recursion** | Нативная с scope isolation | Через code | Через code | Нет |
| **Self-improvement** | Stdlib (inspector → improver) | Нет | Нет | Нет |
| **Discretion** | `**...**` — нативная | Нет | Нет | Нет |
| **Learning curve** | Новый язык (но self-evident) | Python + API | Python + API | Python + API |

---

## 10. Сильные стороны и ограничения

### Сильные стороны

1. **Zero dependencies** — работает в любом AI harness с subagent support
2. **Self-evident syntax** — читается как structured English
3. **Pointer-based context** — VM не раздувается от промежуточных данных
4. **4 state backends** — от ephemeral до PostgreSQL для teams
5. **Self-improvement loop** — stdlib для анализа и улучшения
6. **Persistent agents** — 3 уровня scope с compaction guidelines
7. **Formal grammar** — полная спецификация в compiler.md
8. **Rich examples** — 51 программа от trivial до "build a browser"
9. **Composability** — `use`, `block`, recursion, pipelines, imports from registry

### Ограничения и риски

1. **Недетерминизм**: VM — это LLM, одна программа может исполняться по-разному
2. **Debugging opacity**: если LLM неправильно интерпретирует конструкцию, трассировка непрозрачна
3. **Стоимость**: каждый session = API call. Complex programs = десятки-сотни вызовов
4. **"Prose Complete" порог**: нужен достаточно умный model. Haiku может не справиться с VM simulation
5. **Compiler.md в контексте**: 83KB spec съедает ~30% типичного context window
6. **Нет формальных тестов**: качество зависит от LLM's ability to simulate spec correctly
7. **Нет rate limiting / cost budgets**: встроенных средств ограничения расходов нет
8. **Нет built-in pause/cancel**: зависит от substrate capabilities
9. **Single point of failure**: VM (LLM session) — единственный оркестратор, если падает — нужен resume
10. **Registry dependency**: `use "handle/slug"` зависит от `p.libretto.md` — single point of failure для imports

---

## 11. Рекомендации

### Для standalone проекта

1. **Удалить** openclaw wrapper (index.ts, openclaw.plugin.json, package.json) — уже сделано при копировании
2. **Заменить** "OpenClaw Runtime Mapping" на generic mapping (Task/Read/Write/WebFetch)
3. **Добавить** README.md с quick start
4. **Добавить** Claude Code plugin.json если нужна интеграция

### Заимствования из монорепы

| Паттерн | Источник | Применимость |
|---------|---------|-------------|
| Observer vtable | nullclaw | Pluggable observability для run monitoring |
| Invariant rules | arbiter | Validation constraints для `libretto compile` |
| A11y tree | pinchtab | Browser automation examples |
| HITL gate | plannotator | `input` mid-program approval patterns |

### Оригинальные идеи для развития

1. **Cost budgets**: `budget: $5.00` на уровне программы — VM отслеживает расход и останавливается
2. **Deterministic replay**: сохранять все discretion evaluations для reproducibility
3. **Visual debugger**: web UI для просмотра state.md в реальном времени
4. **Type system для bindings**: optional typing (`let research: ResearchReport = ...`)
5. **Parallel limits**: `parallel (max_concurrent: 3):` для rate limiting

---

*Исследование выполнено 2026-02-23. Источник: openclaw/extensions/libretto → libretto (standalone copy).*
