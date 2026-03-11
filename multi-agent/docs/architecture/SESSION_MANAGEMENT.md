# Session Management — Design & Lifecycle

This document explains the session management layer of MAS: how sessions are created, how user inputs are staged, how execution proceeds across different engines, and how the status state machine works.

---

## 1. Key Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  SESSION LAYER (lib/mas/session/)                       │
│                                                                         │
│  ┌──────────────────────┐   ┌────────────────────────────────────────┐  │
│  │  SessionService      │   │  management/                           │  │
│  │                      │   │    UserSessionManager  — CRUD           │  │
│  │  Application boundary│   │    utils.py            — title helpers  │  │
│  │  stage → execute     │   └────────────────────────────────────────┘  │
│  └──────────┬───────────┘                                               │
│             │                                                           │
│  ┌──────────▼───────────────────────────────────────────────────────┐   │
│  │  execution/                                                      │   │
│  │                                                                  │   │
│  │  SessionInputProjector   — stage inputs, persist (QUEUED)        │   │
│  │  SessionLifecycle         — begin / complete / fail transitions   │   │
│  │  ForegroundSessionRunner  — in-process run & stream              │   │
│  │  BackgroundSessionRunner  — canonical ordering for bg engines    │   │
│  │  BackgroundLifecycleHandler — run_id → record bridge for workers │   │
│  │  BackgroundSessionSubmitter — outbound port (Temporal, Celery…)  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  domain/                                                         │   │
│  │                                                                  │   │
│  │  SessionRecord    — lightweight, persistable dataclass            │   │
│  │  WorkflowSession  — full runtime = SessionRecord + graph + nodes │   │
│  │  SessionStatus    — PENDING → QUEUED → RUNNING → COMPLETED|FAILED│   │
│  │  SessionMeta      — user-facing metadata (title, source, …)      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  building/                                                       │   │
│  │                                                                  │   │
│  │  WorkflowSessionFactory — hydrates SessionRecord → WorkflowSession│  │
│  │                           (resolves blueprint, compiles graph)    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  repository/                                                     │   │
│  │                                                                  │   │
│  │  SessionRepository (ABC)  — save / fetch / list / delete         │   │
│  │  Implemented by MongoSessionRepository (outbound adapter)        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Session Status State Machine

```
     create_session()        projector.apply()       lifecycle.begin()
           │                        │                        │
           ▼                        ▼                        ▼
     ┌─────────┐    stage     ┌──────────┐   begin    ┌──────────┐
     │ PENDING │ ──────────►  │  QUEUED  │ ────────►  │ RUNNING  │
     └─────────┘              └──────────┘            └──────────┘
                                                       │         │
       No turn staged          Turn staged &           │         │
       Empty graph_state       persisted to DB         │         │
       Just a skeleton         UI can read messages    │         │
                                                       ▼         ▼
                                                 ┌──────────┐ ┌──────┐
                                                 │COMPLETED │ │FAILED│
                                                 └──────────┘ └──────┘
```

| Status | Meaning | Set by |
|---|---|---|
| `PENDING` | Session record exists, no user turn staged yet | `UserSessionManager.create_session()` |
| `QUEUED` | User inputs projected onto graph state and persisted. Messages channel has the user prompt. Ready for execution | `SessionInputProjector.apply()` |
| `RUNNING` | Execution engine has started processing the graph | `SessionLifecycle.begin()` |
| `COMPLETED` | Graph finished successfully, final state persisted | `SessionLifecycle.complete()` |
| `FAILED` | Graph execution failed, error recorded | `SessionLifecycle.fail()` |

---

## 3. Two-Phase Execution Pattern

Every execution entry point (`run`, `stream`, `submit`) follows the same two-phase pattern:

```
  Phase 1: STAGE (synchronous, always in the API process)
  Phase 2: EXECUTE (foreground or background, depends on entry point)
```

### Why two phases?

Staging is separated from execution so that:

1. The UI can read the user's message from the database immediately (no waiting for graph completion)
2. Background engines (Temporal, Celery) receive an already-staged record — they never carry raw user inputs
3. The lifecycle component has a single responsibility (execution state transitions) and no input knowledge

### Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  SessionService (all three paths)                        │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              STAGE (identical for all three)                      │  │
│  │                                                                   │  │
│  │   record = manager.get_record(run_id)           ← cheap          │  │
│  │   projector.apply(record, inputs)               ← persist turn   │  │
│  │     • user_prompt seeded into graph_state                         │  │
│  │     • messages has ChatMessage(USER, prompt)                      │  │
│  │     • title derived if missing                                    │  │
│  │     • status = QUEUED                                             │  │
│  │     • repo.save(record)                                           │  │
│  │                                                                   │  │
│  │   ✅ DB now has messages — UI can read them                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│       │                    │                     │                      │
│       ▼                    ▼                     ▼                      │
│                                                                         │
│  ┌──────────┐      ┌──────────────┐      ┌─────────────┐               │
│  │  run()   │      │  stream()    │      │  submit()   │               │
│  │          │      │              │      │             │               │
│  │ hydrate  │      │ hydrate      │      │ hydrate     │               │
│  │ session  │      │ session      │      │ session     │               │
│  │          │      │              │      │             │               │
│  │ begin()  │      │ begin()      │      │ submitter   │               │
│  │ execute  │      │ execute+yield│      │  .submit()  │               │
│  │ complete │      │ complete     │      │             │               │
│  │          │      │              │      │  HTTP 202   │               │
│  │ return   │      │ return       │      │  return     │               │
│  │ result   │      │ iterator     │      │             │               │
│  └──────────┘      └──────────────┘      └──────┬──────┘               │
│                                                  │                      │
│                                     ┌────────────▼───────────┐         │
│                                     │  Background Worker     │         │
│                                     │  (Temporal / Celery)   │         │
│                                     │                        │         │
│                                     │  begin()               │         │
│                                     │  execute_graph()       │         │
│                                     │  complete() / fail()   │         │
│                                     │                        │         │
│                                     │  (no inputs needed —   │         │
│                                     │   already staged)      │         │
│                                     └────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Responsibilities (SRP)

| Component | Single Responsibility |
|---|---|
| `SessionInputProjector` | Map raw external inputs to graph state channels, mirror prompt → messages, derive title, transition to QUEUED, persist |
| `SessionLifecycle` | Manage execution state transitions: begin (→ RUNNING), complete (→ COMPLETED), fail (→ FAILED). No input knowledge |
| `ForegroundSessionRunner` | Orchestrate in-process execution: begin → run graph → complete/fail. Manages streaming channels |
| `BackgroundSessionRunner` | Define canonical ordering for background engines: begin → execute_graph → complete/fail |
| `BackgroundLifecycleHandler` | Bridge run_id strings (what workers have) to SessionRecord objects (what lifecycle needs) |
| `SessionService` | Application use-case boundary: coordinates stage → execute across all entry points |
| `UserSessionManager` | CRUD operations: create, get_record, get_session, list, delete |
| `WorkflowSessionFactory` | Hydrate a lightweight SessionRecord into a full WorkflowSession (resolve blueprint, compile graph) |

---

## 5. SessionRecord vs WorkflowSession

```
  SessionRecord (lightweight, persistable)
  ┌──────────────────────────────────────┐
  │  run_id                              │
  │  user_id                             │
  │  blueprint_id                        │
  │  run_context (RunContext)            │
  │  metadata (SessionMeta)             │
  │  graph_state (GraphState)           │
  │  status (SessionStatus)             │
  └──────────────────────────────────────┘
                    │
                    │  composition
                    ▼
  WorkflowSession (full runtime)
  ┌──────────────────────────────────────┐
  │  record: SessionRecord  ◄──────────── persistable state
  │  session_registry       ◄──────────── node/LLM instances
  │  rt_graph_plan          ◄──────────── compiled plan
  │  executable_graph       ◄──────────── graph executor
  │  builder                ◄──────────── graph builder
  └──────────────────────────────────────┘
```

- `SessionRecord` is cheap to create and fetch. Used for persistence, lifecycle transitions, and status queries.
- `WorkflowSession` is expensive to build (requires blueprint resolution and graph compilation). Only created when execution is needed.

---

## 6. UserQuestionNode Idempotency

The `UserQuestionNode` is the first node in most graphs. It promotes `user_prompt` into the `messages` conversation channel.

Since `SessionInputProjector` already stages the user prompt into `messages` before execution starts, the node includes an idempotency guard:

```
UserQuestionNode.run(state):
    prompt = state[USER_PROMPT]

    if last message is already this prompt → skip
    else → promote_to_messages(prompt)
```

This ensures:
- No duplicate messages when the projector has already staged the turn
- The graph remains self-contained: if run without `SessionService` (e.g., in tests), `UserQuestionNode` still adds the prompt

---

## 7. Adding a New Background Engine

To add a new background engine (e.g., Celery), implement:

1. **`BackgroundSessionOps`** (Protocol) — four async methods: `begin`, `execute_graph`, `complete`, `fail`
2. **`BackgroundSessionSubmitter`** (ABC) — one method: `submit(session, request) → handle_id`

The canonical ordering (`begin → execute → complete/fail`) is enforced by `BackgroundSessionRunner` in the domain layer. Your engine only supplies the **how**, never the **when**.

```
  Your Celery task:
      runner = BackgroundSessionRunner()
      await runner.run(self)    ← self implements BackgroundSessionOps

  That's it. The ordering is not your responsibility.
```
