# Enterprise Execution Planner (ADOS OS 4.3)

ChatGPT is the Architect. ADOS is the Executive Operating System.

The Execution Planner receives one engineering specification and turns it into executable work packages for registered Orchestrator agents. It does **not** invent architecture — it executes the given plan.

```
User → ChatGPT (architecture) → Execution Planner → AI Orchestrator
  → Developer / UI / Docs / QA / Review / Build / Deploy agents
  → Cursor · Claude · Runtime · Git · Tests · Build
```

## Module

`src/execution` · service `ados.execution` · `@ados/execution` 4.3.0

| Component | Role |
|-----------|------|
| `ExecutionPlanner` | Facade |
| `ExecutionPlan` | Plan + task graph |
| `TaskAnalyzer` | Spec structure analysis |
| `TaskSplitter` | Role-based work packages |
| `DependencyResolver` | Order + parallel waves |
| `ExecutionQueue` | Ready/running/blocked queue |
| `ExecutionScheduler` | Parallel Orchestrator runs |
| `ExecutionMonitor` | Live progress |
| `ExecutionValidator` | Completion checks |
| `ExecutionReporter` | Final engineering report |
| `ExecutionHistory` | Audit history |

## Engineering specification

```json
{
  "mission": "...",
  "objective": "...",
  "requirements": [],
  "files": [],
  "modules": [],
  "tests": [],
  "acceptanceCriteria": []
}
```

## Agent mapping (reuse Orchestrator)

| Role | Agent |
|------|-------|
| developer / ui | `agent.developer` |
| documentation | `agent.research` |
| qa | `agent.qa` |
| review | `agent.reviewer` |
| build / deploy | `agent.automation` |

## Parallel execution

Wave 1: Developer · UI · Documentation (independent)  
Wave 2: Review · QA (after implementation)  
Wave 3: Build  
Wave 4: Deploy (optional)

## REST

| Method | Path |
|--------|------|
| POST | `/execution/plan` |
| GET | `/execution/status` |
| GET | `/execution/history` |
| GET | `/execution/report` |

## Events

`plan.created` · `plan.started` · `task.assigned` · `task.started` · `task.completed` · `task.failed` · `plan.completed`

## Control Center

**Execution Planner** (`/execution`): current plan, graph, running agents, completed/blocked tasks, logs, report, history.

## Example

```bash
curl -s -X POST http://localhost:3000/execution/plan \
  -H 'Content-Type: application/json' \
  -d '{"autoRun":true,"mission":"Ship feature","objective":"Implement X","requirements":["A"],"files":["src/a.ts"],"modules":["src"],"tests":["unit"],"acceptanceCriteria":["Done"]}'
```
