# MAS — Architecture Overview

This document describes the internal architecture of the Multi-Agent System (MAS). It covers every layer, abstraction, data flow, and dependency rule.

---

## 1. System Layers

MAS follows hexagonal architecture (ports and adapters). The domain core has zero knowledge of any external framework. All technology bindings live in adapter layers. A single composition root wires everything together.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL WORLD                                 │
│                                                                             │
│    HTTP Clients          Temporal Server         MongoDB         Redis       │
└────────┬────────────────────┬──────────────────────┬───────────────┬────────┘
         │                    │                      │               │
         ▼                    ▼                      ▼               ▼
┌─────────────────┐  ┌────────────────┐   ┌────────────────────────────────┐
│ INBOUND ADAPTERS│  │SHARED TEMPORAL │   │     OUTBOUND ADAPTERS          │
│                 │  │  models.py     │   │                                │
│  Flask API      │  │  client.py     │   │  Temporal executor/builder     │
│  Temporal Worker│  └────────────────┘   │  LangGraph executor/builder    │
└────────┬────────┘                       │  Mongo repositories            │
         │                                │  Redis/Local channels          │
         │                                └───────────────┬────────────────┘
         │                                                │
         │              ALL DEPEND INWARD                  │
         └─────────────────────┬──────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                        DOMAIN CORE  (lib/mas/)                              │
│                                                                             │
│  Pure Python. No Flask, Temporal, Redis, Mongo, or LangGraph imports.       │
│  Everything above depends on this. This depends on nothing above.           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         ▲
         │
┌────────┴────────────────────────────────────────────────────────────────────┐
│                     COMPOSITION ROOT  (bootstrap/)                          │
│                                                                             │
│  AppContainer — the ONE place that knows both domain AND adapters.          │
│  Reads config, instantiates all services, injects adapters into ports.      │
│  No domain or adapter code ever imports this module.                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Domain Core — Internal Structure

```
lib/mas/
│
├── core/                    THE FOUNDATION
│   ├── enums                  ResourceCategory (NODE, LLM, TOOL, CONDITION, ...)
│   ├── run_context            RunContext (user, scope, engine, timestamps)
│   ├── context                ContextVar-based thread-local RunContext access
│   ├── channels/              Streaming abstractions (ABCs):
│   │     SessionChannel         write:  emit(data), close()
│   │     SessionChannelReader   read:   __iter__() → Optional[dict]
│   │     SessionStreamMonitor   query:  get_status(), list_active()
│   │     ChannelFactory         create(), create_reader(), create_monitor()
│   │     StreamEmitter          low-level emission for LangGraph
│   ├── iem/                   Inter-Element Messaging (task packets between agents)
│   └── models                 ElementCard (identity + capabilities of an element)
│
├── elements/                PLUGGABLE CATALOG
│   ├── common/                BaseElementSpec, BaseFactory (spec → instance)
│   ├── nodes/                 orchestrator, custom_agent, a2a_agent, user_question,
│   │                          final_answer, llm_merger, branch_chooser, mock_agent
│   ├── llms/                  openai, google_genai, mock
│   ├── tools/                 web_fetch, ssh_exec, oc_exec, mcp_proxy, builtin
│   ├── conditions/            router_boolean, router_direct, threshold
│   ├── retrievers/            docs_rag, docs_dataflow, slack
│   └── providers/             a2a_client, mcp_server_client, rag_client
│
├── catalog/                 DISCOVERY
│   └── ElementRegistry        singleton; auto-discovers all element specs at startup
│                              keyed by (ResourceCategory, type_key)
│
├── blueprints/              BLUEPRINT MANAGEMENT
│   ├── models/                BlueprintDraft → BlueprintSpec (resolved)
│   │                          StepDef, ResourceSpec, BlueprintResource
│   ├── loader/                JSON/YAML parsing
│   ├── resolver/              $ref resolution (shared resources → inline config)
│   ├── repository/            BlueprintRepository (ABC)
│   └── service                BlueprintService (CRUD, validation)
│
├── graph/                   GRAPH DATA STRUCTURES
│   ├── state/
│   │   ├── GraphState           execution state shared across all nodes
│   │   ├── channel_types        BaseStateChannel, LastValueChannel, BinOpChannel
│   │   └── merge_strategies     merge_string_dicts, append_chat_messages, ...
│   ├── models/
│   │   ├── Step                 logical step (uid, rid, after[], condition, branches)
│   │   ├── RTStep               Step + bound node callable + condition callable
│   │   ├── StepContext           runtime context injected into each node
│   │   └── AdjacentNodes         neighboring node identity cards
│   ├── graph_plan               GraphPlan (ordered list of Steps)
│   ├── rt_graph_plan            RTGraphPlan (GraphPlan + SessionRegistry → RTSteps)
│   ├── plan_builder             PlanBuilder (BlueprintSpec → GraphPlan)
│   ├── topology/                graph analysis (finalizer paths, connectivity)
│   └── validation/              cycle detection, orphan checks, required nodes
│
├── engine/                  GRAPH EXECUTION
│   ├── domain/
│   │   ├── BaseGraphExecutor    ABC: run(), stream(), get_state()
│   │   ├── BaseGraphBuilder     ABC: add_node(), add_edge(), build_executor()
│   │   │                        + compile_from_plan() template method
│   │   ├── GraphDefinition      serializable graph topology (NodeDef, edges, conditionals)
│   │   ├── types                ExecuteNodeFn, EvaluateConditionFn (callback protocols)
│   │   └── errors               GraphRecursionError
│   ├── distributed/
│   │   ├── GraphTraversal       BSP superstep algorithm
│   │   ├── NodeExecutor         rebuild node from mini-blueprint on any worker, run it
│   │   └── serialization        NodeDeploymentSerializer (RTGraphPlan → GraphDefinition)
│   └── factory                  GraphBuilderFactory (lazy: "temporal" → builder, ...)
│
├── session/                 SESSION LIFECYCLE
│   ├── domain/
│   │   ├── WorkflowSession       the central entity (registry + plan + executor + state)
│   │   ├── SessionStatus         PENDING → RUNNING → COMPLETED / FAILED
│   │   ├── SessionRegistry       live element instances keyed by (category, rid)
│   │   └── dto/models            ChatHistoryItem, SessionMeta, analytics models
│   ├── building/
│   │   ├── WorkflowSessionFactory  BlueprintSpec → WorkflowSession (full pipeline)
│   │   └── SessionElementBuilder   BlueprintSpec → SessionRegistry
│   ├── management/
│   │   └── UserSessionManager      CRUD: create, get, list, delete, stats
│   ├── repository/
│   │   └── SessionRepository       ABC: save, fetch, list, count, analytics
│   ├── execution/
│   │   ├── SessionLifecycle               state machine: prepare / complete / fail
│   │   ├── ForegroundSessionRunner        run() + stream() for in-process engines
│   │   ├── BackgroundSessionRunner        enforces prepare → execute → complete/fail
│   │   ├── BackgroundSessionOps           protocol that background engines implement
│   │   ├── BackgroundLifecycleHandler     fetch session + lifecycle + close channel
│   │   └── BackgroundSessionSubmitter     port for fire-and-forget submission
│   └── service                            SessionService (application facade)
│
├── resources/               shared resource management
├── actions/                 external action providers
├── templates/               blueprint templates
├── sharing/                 session cloning
├── statistics/              usage stats
└── validation/              cross-cutting element validation
```

---

## 3. Adapter Layer

```
adapters/
│
├── temporal/                  SHARED TEMPORAL INFRASTRUCTURE
│   ├── models.py                Pydantic DTOs for workflow/activity params
│   └── client.py                get_temporal_client() factory
│
├── inbound/                   RECEIVE WORK
│   ├── flask/
│   │   ├── flask_app.py           create_app(container) factory
│   │   ├── endpoints/             RPC-style route handlers (sessions, blueprints, ...)
│   │   └── streaming/             HeartbeatStream (idle keepalives)
│   └── temporal/
│       ├── worker.py              run_worker() — builds activities, starts Worker
│       ├── workflows/
│       │   ├── SessionWorkflow              parent: lifecycle + graph as child
│       │   └── GraphTraversalWorkflow       BSP loop, each node = activity call
│       └── activities/
│           ├── GraphNodeActivities          execute_graph_node, evaluate_condition
│           └── SessionLifecycleActivities   prepare, complete, fail
│
└── outbound/                  CALL EXTERNAL SYSTEMS
    ├── temporal/
    │   ├── executor.py            TemporalGraphExecutor (start workflow, block/return)
    │   ├── builder.py             TemporalGraphBuilder (RTGraphPlan → GraphDefinition)
    │   └── submitter.py           TemporalSessionSubmitter (fire-and-forget)
    ├── langgraph/
    │   ├── executor.py            LangGraphExecutor (in-process invoke/stream)
    │   ├── builder.py             LangGraphBuilder (StateGraph → compiled graph)
    │   └── emitter.py             LangGraphEmitter (StreamEmitter for callbacks)
    ├── channels/
    │   ├── local/
    │   │   ├── channel.py           LocalSessionChannel (in-process, delegates to emitter)
    │   │   └── factory.py           LocalChannelFactory
    │   └── redis/
    │       ├── channel.py           RedisSessionChannel (XADD to stream)
    │       ├── reader.py            RedisSessionChannelReader (XREAD, replay + live)
    │       ├── monitor.py           RedisStreamMonitor (XINFO, SMEMBERS)
    │       ├── factory.py           RedisChannelFactory
    │       └── constants.py         stream keys, field names, control signals
    └── mongo/
        ├── session_repository.py    MongoSessionRepository
        ├── blueprint_repository.py  MongoBlueprintRepository
        ├── resource_repository.py   MongoResourceRepository
        ├── share_repository.py      MongoShareRepository
        └── template_repository.py   MongoTemplateRepository
```

---

## 4. Dependency Rules

```
                           ┌─────────┐
                           │bootstrap │  can import EVERYTHING
                           │container │  (the only place that does)
                           └────┬─────┘
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
          ┌───────────┐  ┌───────────┐  ┌──────────────┐
          │  inbound   │  │  shared   │  │   outbound    │
          │  adapters  │  │ temporal/ │  │   adapters    │
          └─────┬──────┘  └─────┬─────┘  └──────┬───────┘
                │               │               │
                └───────┬───────┴───────┬───────┘
                        ▼               ▼
                  ┌───────────────────────────┐
                  │       lib/mas/ (domain)    │
                  │                           │
                  │  NEVER imports adapters   │
                  │  NEVER imports bootstrap  │
                  │  Only stdlib + pydantic   │
                  └───────────────────────────┘

  FORBIDDEN:
    inbound  ──✗──▶  outbound       (and vice versa)
    domain   ──✗──▶  adapters
    domain   ──✗──▶  bootstrap
    adapters ──✗──▶  bootstrap
```

---

## 5. How a Blueprint Becomes an Executable Session

```
BlueprintDraft (JSON from UI/API)
    │
    │  BlueprintResolver: resolve $ref → inline configs
    ▼
BlueprintSpec (fully resolved)
    │
    │  PlanBuilder: extract steps, edges, conditions from spec
    ▼
GraphPlan (logical: list of Step[uid, rid, after[], condition, branches])
    │
    │  SessionElementBuilder: instantiate all elements from their specs
    ▼
SessionRegistry (live instances keyed by category + rid)
    │
    │  RTGraphPlan: bind callables to steps, inject StepContext
    ▼
RTGraphPlan (RTStep = Step + node_callable + condition_callable)
    │
    │  GraphBuilderFactory → BaseGraphBuilder.compile_from_plan()
    │
    ├── LangGraphBuilder                 TemporalGraphBuilder
    │   StateGraph.add_node/edge/...     NodeDeploymentSerializer
    │   .compile()                       → GraphDefinition (serializable)
    │   → LangGraphExecutor              → TemporalGraphExecutor
    ▼
WorkflowSession
  ├── session_registry    live element instances
  ├── rt_graph_plan       plan with bound callables
  ├── executable_graph    LangGraphExecutor or TemporalGraphExecutor
  ├── graph_state         GraphState (mutable execution state)
  ├── run_context         RunContext (user, scope, engine)
  ├── status              PENDING → RUNNING → COMPLETED / FAILED
  └── metadata            title, tags, ...
```

---

## 6. GraphState and Channel Merge System

GraphState is a Pydantic model representing the shared mutable state that flows through the graph. Each field has an associated merge strategy that determines how concurrent writes are reconciled.

```
GraphState
┌──────────────────────────────────────────────────────────────────┐
│  Field              Merge Strategy            Channel Type       │
│  ─────              ──────────────            ────────────       │
│  user_prompt        last write wins           LastValueChannel   │
│  output             last write wins           LastValueChannel   │
│  target_branch      last write wins           LastValueChannel   │
│  nodes_output       merge dicts               BinOpChannel       │
│  messages           append                    BinOpChannel       │
│  dynamic_fields     update dict               BinOpChannel       │
│  inter_packets      append                    BinOpChannel       │
│  task_threads       merge                     BinOpChannel       │
│  threads            merge                     BinOpChannel       │
│  workspaces         merge                     BinOpChannel       │
└──────────────────────────────────────────────────────────────────┘

When multiple nodes run in parallel (same superstep), each writes
to its own copy. The UPDATE phase reconciles writes through channels:

  Node A writes output="hello"  ─┐
  Node B writes output="world"  ─┼── LastValueChannel → last one wins
  Node C writes output="!"      ─┘

  Node A writes messages=[m1]   ─┐
  Node B writes messages=[m2]   ─┼── BinOpChannel(append) → [m1, m2, m3]
  Node C writes messages=[m3]   ─┘
```

---

## 7. Graph Traversal — BSP Superstep Algorithm

The traversal follows the Pregel / Bulk Synchronous Parallel model, inspired by LangGraph. Callbacks decouple the algorithm from the execution infrastructure.

```
                         entry node
                             │
                     ┌───────▼───────┐
                     │   SUPERSTEP   │◀────────────────────────────┐
                     └───────┬───────┘                             │
                             │                                     │
                  ┌──────────▼──────────┐                          │
                  │       PLAN          │                          │
                  │                     │  none ready              │
                  │  Find nodes whose   │──────────▶ DONE          │
                  │  ALL predecessors   │                          │
                  │  have executed      │  step > limit            │
                  │                     │──────────▶ RECURSION ERR │
                  └──────────┬──────────┘                          │
                             │ ready = {A, B, C}                   │
                  ┌──────────▼──────────┐                          │
                  │      EXECUTE        │                          │
                  │                     │                          │
                  │  Run all ready      │                          │
                  │  nodes in PARALLEL  │                          │
                  │  against SAME state │                          │
                  │  snapshot           │                          │
                  └──────────┬──────────┘                          │
                             │ results                             │
                  ┌──────────▼──────────┐                          │
                  │      UPDATE         │                          │
                  │                     │                          │
                  │  For each field:    │                          │
                  │    extract writes   │                          │
                  │    apply merge      │                          │
                  │                     │                          │
                  │  Resolve next nodes │                          │
                  │  (edges + condition │                          │
                  │   + predecessor     │                          │
                  │   gate)             │                          │
                  └──────────┬──────────┘                          │
                             └─────────────────────────────────────┘

Example:

  Graph:  entry → [A, B, C] → D → exit

  Superstep 0: {entry}         run entry
  Superstep 1: {A, B, C}      all predecessors done → parallel
  Superstep 2: {D}             waited for A, B, C
  Superstep 3: {exit}          done
```

The algorithm is engine-agnostic. It receives two callbacks:
- `ExecuteNodeFn` — run a single node (in-process call or Temporal activity)
- `EvaluateConditionFn` — evaluate a conditional edge

This allows the same traversal code to power both LangGraph and Temporal.

---

## 8. Execution Modes

### Mode 1: `run()` — synchronous, blocking

```
Client ──POST {stream:false}──▶ Flask
                                  │
                            SessionService.run()
                                  │
                          ForegroundSessionRunner.run()
                                  │
                   ┌──────────────┼──────────────┐
                   ▼                              ▼
           LangGraph engine               Temporal engine
           executor.run()                 executor.run()
           (in-process)                   (blocks until workflow done)
                   └──────────────┬──────────────┘
                                  ▼
                          ◀── JSON response ──▶ Client

Lifecycle: prepare → execute → complete (all in Flask process)
```

### Mode 2: `stream()` — synchronous, NDJSON streaming

```
Client ──POST {stream:true}──▶ Flask
                                  │
                          ForegroundSessionRunner.stream()
                                  │
                   1. prepare()
                   2. channel = factory.create(session_id)
                   3. inject channel into in-memory node objects
                   4. for chunk in executor.stream():
                        yield chunk ──NDJSON──▶ Client
                   5. complete(), channel.close()

Works with LangGraph (nodes are in the same process).
```

### Mode 3: `submit()` — fire-and-forget (Temporal)

```
Client ──POST──▶ Flask
                   │
          TemporalSessionSubmitter.submit()
             start_workflow("SessionWorkflow", params)
                   │
            ◀── 202 {workflowId} ──▶ Client


═══ ON TEMPORAL WORKER (later) ═══════════════════════════════════

SessionWorkflow.run(params)
    │
    ▼
BackgroundSessionRunner.run(ops=self)
    │
    ├── ops.prepare()       → activity → BackgroundLifecycleHandler
    │                                      → SessionLifecycle.prepare()
    │
    ├── ops.execute_graph() → child GraphTraversalWorkflow
    │                           → GraphTraversal.run() (BSP loop)
    │                             each node = activity call
    │                             → GraphNodeActivities.execute_node()
    │                               → factory.create(session_id) → channel
    │                               → NodeExecutor.execute_node(channel)
    │                               → node emits to channel
    │
    └── ops.complete()      → activity → BackgroundLifecycleHandler
                                          → SessionLifecycle.complete()
                                          → channel.close()


═══ CLIENT SUBSCRIBES SEPARATELY ═════════════════════════════════

Client ──GET /session.subscribe──▶ Flask
                                     │
                            factory.create_reader(session_id)
                            RedisChannelReader: XREAD (replay + live)
                                     │
                            ◀── NDJSON stream ──▶ Client
                            (closes when channel.close() signal received)
```

---

## 9. Streaming and Channel Architecture

```
                    NODE EXECUTION
                    (any engine, any process)
                         │
                    node.emit(data)
                         │
                         ▼
                  SessionChannel.emit()
                         │
          ┌──────────────┴──────────────┐
          ▼                              ▼
  LocalSessionChannel             RedisSessionChannel
  (in-process)                    (cross-process)
  ┌──────────────┐                ┌──────────────────────┐
  │ delegates to │                │ XADD                  │
  │ StreamEmitter│                │ mas:stream:{id}       │
  │ (LangGraph   │                │ {payload: JSON(data)} │
  │  callback)   │                │                       │
  └──────┬───────┘                │ on close():           │
         │                        │   XADD {__control:    │
         ▼                        │         close}        │
  Flask reads from                │   SREM active set     │
  LangGraph stream                │   EXPIRE (TTL)        │
  iterator directly               └──────────┬───────────┘
         │                                   │
         ▼                        ┌──────────┴──────────┐
  NDJSON to client                ▼                     ▼
                          ChannelReader           StreamMonitor
                          XREAD (blocking)        XINFO STREAM
                          replay from "0"         SMEMBERS active
                          yields dict | None
                                  │                     │
                                  ▼                     ▼
                          NDJSON stream           JSON metadata
                          to client               {event_count,
                                                   is_active, ...}


ChannelFactory creates all three components:
  create(session_id)         → SessionChannel      always available
  create_reader(session_id)  → ChannelReader        Redis only (None for local)
  create_monitor()           → StreamMonitor        Redis only (None for local)
```

Data transparency: channels never modify user data. What a node emits is exactly what the client receives. Control signals (close) use a separate Redis Stream field.

---

## 10. Session Lifecycle State Machine

```
                 create()
                    │
                    ▼
              ┌──────────┐
              │ PENDING   │
              └─────┬─────┘
                    │  prepare()
                    │  seed inputs, bind context, persist
                    ▼
              ┌──────────┐
              │ RUNNING   │
              └─────┬─────┘
                    │
           ┌───────┴───────┐
           │               │
      success           failure
           │               │
           ▼               ▼
    ┌───────────┐   ┌──────────┐
    │ COMPLETED │   │  FAILED  │
    └───────────┘   └──────────┘
     complete()       fail()
     attach state     mark failed
     persist          persist

SessionLifecycle owns these transitions. It is stateless —
all state lives in WorkflowSession and the repository.

Called by ForegroundSessionRunner (in-process) or
BackgroundLifecycleHandler (on worker). Same logic, different caller.
```

---

## 11. Background Execution — The 5 Pieces

Background session execution is split into 5 components, each with one clear role:

```
  ⑤ Submitter  ──▶  ④ BackgroundSessionRunner
                           │
                           │ calls in order:
                           │
                      ③ Ops (Protocol)
                           │
              ┌────────────┼────────────┐
              │            │            │
           prepare    execute_graph  complete/fail
              │            │            │
              ▼            ▼            ▼
   ② LifecycleHandler   (graph)   ② LifecycleHandler
              │                        │
              ▼                        ▼
         ① Lifecycle              ① Lifecycle
```

### What each piece does — one sentence

| # | Name | Role |
|---|------|------|
| ① | **SessionLifecycle** | Changes session status in the database (RUNNING, COMPLETED, FAILED) |
| ② | **BackgroundLifecycleHandler** | Fetches session from DB by run_id, calls Lifecycle, closes the stream |
| ③ | **BackgroundSessionOps** | A contract: "your engine must provide these 4 methods" |
| ④ | **BackgroundSessionRunner** | Calls the 4 methods in the correct order, catches errors |
| ⑤ | **BackgroundSessionSubmitter** | Sends "start this session" from Flask to the worker |

### Detailed breakdown

```
┌────────────────────────────────────────────────────────────────────┐
│  ⑤ BackgroundSessionSubmitter (ABC)                                │
│                                                                    │
│  Called from Flask when user hits POST /submit.                    │
│  Packages the session, starts the remote workflow, returns a       │
│  handle ID immediately. Flask responds 202.                        │
│                                                                    │
│  submit(session, request) → str (workflow/task handle)             │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 │  (network boundary)
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│  ④ BackgroundSessionRunner                                         │
│                                                                    │
│  The ordering rule. Ensures lifecycle steps happen in sequence:     │
│                                                                    │
│  async run(ops):                                                   │
│      try:                                                          │
│          seeded = await ops.prepare()                               │
│          final  = await ops.execute_graph(seeded)                  │
│          await ops.complete(final)                                 │
│      except:                                                       │
│          await ops.fail(e)                                         │
│                                                                    │
│  Mirrors ForegroundSessionRunner for the background path.          │
└────────────────────────────────┬───────────────────────────────────┘
                                 │ calls ops.*()
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│  ③ BackgroundSessionOps (Protocol)                                 │
│                                                                    │
│  Contract that every background engine implements:                 │
│                                                                    │
│    prepare()          → dict      seed state                       │
│    execute_graph()    → dict      run the graph                    │
│    complete()         → None      finalize                         │
│    fail()             → None      handle error                     │
│                                                                    │
│  Temporal impl: SessionWorkflow (each method → activity or child)  │
│  Future impls:  CeleryTask, RQJob, ... (direct function calls)    │
└───────┬───────────────────────────────────────────┬────────────────┘
        │ prepare / complete / fail                 │ execute_graph
        │ → activities                              │ → child workflow
        ▼                                           ▼
┌──────────────────────────┐          ┌──────────────────────────────┐
│  ② BackgroundLifecycle   │          │  GraphTraversalWorkflow      │
│     Handler              │          │                              │
│                          │          │  BSP superstep loop          │
│  Bridges run_id strings  │          │  (plan → execute → update)   │
│  to WorkflowSession      │          │  Each node = activity call   │
│  objects:                │          │  → NodeExecutor              │
│                          │          │  → emit to channel           │
│  1. Fetch from DB        │          └──────────────────────────────┘
│  2. Call Lifecycle ①     │
│  3. Close channel        │
│                          │
│  Does NOT execute the    │
│  graph.                  │
└───────────┬──────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────────────┐
│  ① SessionLifecycle                                                │
│                                                                    │
│  The atomic state transitions (lowest level):                      │
│                                                                    │
│  prepare(session, inputs)  → seed inputs, mark RUNNING, save       │
│  complete(session, state)  → attach state, mark COMPLETED, save    │
│  fail(session, error)      → mark FAILED, save                     │
│                                                                    │
│  Shared by BOTH ForegroundSessionRunner and BackgroundLifecycle-   │
│  Handler. Knows nothing about engines, channels, or workers.       │
└────────────────────────────────────────────────────────────────────┘
```

### How they chain together (Temporal)

```
User clicks "Run"
       │
       ▼
  ⑤ TemporalSessionSubmitter.submit()
       │  → start_workflow() → returns 202 to user
       │
       ╰──── Temporal Worker ────▶  SessionWorkflow.run()
                                         │
                                    ④ BackgroundSessionRunner.run(self)
                                         │
                        ┌────────────────┼────────────────┐
                        │                │                │
                     prepare()     execute_graph()   complete()
                        │                │                │
                        ▼                ▼                ▼
                   activity         child workflow    activity
                        │           (graph runs)         │
                        ▼                                ▼
                   ② Handler                        ② Handler
                    .prepare()                       .complete()
                        │                                │
                        ▼                                ▼
                   ① Lifecycle                      ① Lifecycle
                   RUNNING                          COMPLETED
                                                    + close stream
```

### Adding a new engine

Implement `BackgroundSessionOps` + `BackgroundSessionSubmitter`. The runner, lifecycle handler, and lifecycle are reused as-is.

---

## 12. Temporal Worker — Internal Wiring

```
mas worker --threads 20
     │
     ▼
_build_container() → AppContainer
     │
     ▼
run_worker(container, threads)
     │
     │  Build activity instances using container's domain services:
     │
     ├── NodeExecutor(session_factory)
     │
     ├── GraphNodeActivities(node_executor, channel_factory)
     │     execute_graph_node  → create channel → NodeExecutor.execute_node()
     │     evaluate_condition  → NodeExecutor.evaluate_condition()
     │
     ├── BackgroundLifecycleHandler(session_manager, lifecycle, channel_factory)
     │
     ├── SessionLifecycleActivities(lifecycle_handler)
     │     prepare_session   → BackgroundLifecycleHandler.prepare()
     │     complete_session  → BackgroundLifecycleHandler.complete()
     │     fail_session      → BackgroundLifecycleHandler.fail()
     │
     └── Worker(
           workflows  = [GraphTraversalWorkflow, SessionWorkflow]
           activities = [execute_graph_node, evaluate_condition,
                        prepare_session, complete_session, fail_session]
           thread_pool = ThreadPoolExecutor(max_workers=threads)
         )

Workflows call activities by STRING NAME (deterministic replay safe).
Activities are thin one-liner delegates to domain services.
```

---

## 13. Element Discovery and Instantiation

```
Startup: ElementRegistry.auto_discover()
     │
     │  Scans mas/elements/{nodes,llms,tools,conditions,retrievers,providers}/
     │  Finds all BaseElementSpec subclasses, registers by (category, type_key)
     ▼
ElementRegistry (singleton)
┌──────────────────────────────────────────────────┐
│  NODE:      orchestrator, custom_agent, a2a, ... │
│  LLM:       openai, google_genai, mock           │
│  TOOL:      web_fetch, ssh_exec, oc_exec, ...    │
│  CONDITION: router_boolean, router_direct, ...   │
│  RETRIEVER: docs_rag, docs_dataflow, slack       │
│  PROVIDER:  a2a_client, mcp_server_client, ...   │
└──────────────────────────────────────────────────┘

At session creation time:

  BlueprintSpec lists which elements to use
         │
         ▼
  SessionElementBuilder.build(blueprint_spec)
         │
         │  For each element in spec:
         │    spec_cls = registry.get_spec(category, type_key)
         │    factory  = spec_cls.get_factory()
         │    instance = factory.create(config)
         ▼
  SessionRegistry
  ┌────────────────────────────────────────────┐
  │  (NODE, "agent_1")    → <CustomAgent>      │
  │  (NODE, "orch_0")     → <OrchestratorNode> │
  │  (LLM,  "gpt4o")     → <OpenAILLM>        │
  │  (TOOL, "web_fetch")  → <WebFetchTool>     │
  │  (CONDITION, "r1")    → <RouterBoolean>    │
  └────────────────────────────────────────────┘
```

---

## 14. Composition Root — What Gets Wired

```
AppContainer(AppConfig)
│
├── ElementRegistry.auto_discover()
├── ActionsService.auto_discover_actions()
│
├── CatalogService(element_registry)
├── GraphService(element_registry)
├── GraphValidationService(element_registry)
│
├── MongoBlueprintRepository(db, coll)           outbound adapter
├── MongoResourceRepository(...)                  outbound adapter
├── MongoSessionRepository(...)                   outbound adapter
├── MongoShareRepository(...)                     outbound adapter
├── MongoTemplateRepository(...)                  outbound adapter
│
├── ResourcesRegistry(repo, bp_repo)
├── ResourcesService(registry, elements, validation)
├── BlueprintResolver(resources, elements)
├── BlueprintService(repo, resolver, validation)
│
├── WorkflowSessionFactory(elements, engine_name)
├── UserSessionManager(repo, factory, blueprints)
├── SessionLifecycle(repo)
│
├── ChannelFactory                                config-driven
│     redis_url set → RedisChannelFactory(url, ttl, block_ms, batch_size)
│     otherwise     → LocalChannelFactory()
│
├── ForegroundSessionRunner(lifecycle, channel_factory)
│
├── BackgroundSessionSubmitter                    engine-driven
│     engine=temporal → TemporalSessionSubmitter()
│     otherwise       → None
│
├── SessionService(manager, foreground_runner, background_submitter)
│
├── ShareCloner, ShareService
├── StatisticsService
└── TemplateService
```

---

## 15. API Surface

```
/api/
├── /health/                                  GET   health check
│
├── /sessions/
│   ├── user.session.create      POST         create session from blueprint
│   ├── user.session.execute     POST         run or stream (foreground)
│   ├── user.session.submit      POST         fire-and-forget (background)
│   ├── session.state.get        GET          final graph state
│   ├── session.status.get       GET          session status
│   ├── session.delete           DELETE       delete session
│   ├── session.user.chat.get    GET          chat history
│   ├── session.subscribe        GET          NDJSON event stream (Redis)
│   ├── session.stream.status    GET          stream metadata
│   └── session.stream.active    GET          list running sessions
│
├── /blueprints/                              CRUD + validation
├── /catalog/                                 element discovery
├── /resources/                               shared resources
├── /graph/                                   graph structure
├── /graph/validation/                        graph validation
├── /actions/                                 external actions
├── /shares/                                  session sharing
├── /statistics/                              usage stats
└── /templates/                               blueprint templates
```

---

## 16. Adding a New Execution Engine

To add a new engine (e.g., Celery), implement these domain contracts:

1. **`BaseGraphBuilder`** — convert RTGraphPlan into your engine's executable.
2. **`BaseGraphExecutor`** — `run()` and `stream()` against your engine.
3. **`BackgroundSessionSubmitter`** — fire-and-forget submission port.
4. **`BackgroundSessionOps`** — protocol with prepare/execute/complete/fail.

Register the builder in `GraphBuilderFactory` and wire the submitter in `AppContainer`. The runner, lifecycle handler, traversal algorithm, node executor, and channel system are all reusable.
