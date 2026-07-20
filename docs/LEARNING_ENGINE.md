# Platform Learning & Feedback Engine

> Sprint 4.4 — continuous improvement from execution history and feedback

## Overview

The Platform Learning & Feedback Engine is a **reusable learning subsystem** that continuously improves agent behavior using execution history, user feedback, and workflow outcomes.

**No LLM dependency. No modifications to Sprint 1–4.3 architecture.**

---

## Architecture

```mermaid
flowchart TB
    subgraph Learning Layer
        LE[LearningEngine]
        LP[LearningPipeline]
        FC[FeedbackCollector]
        ES[ExperienceStore]
        PA[PatternAnalyzer]
        RE[RecommendationEngine]
        LM[LearningMetrics]
    end

    subgraph Feedback Sources
        WF[Workflow results]
        TK[Task results]
        HF[Human feedback]
        AE[Agent self-evaluation]
        TE[Tool execution]
        SE[System events]
        ER[Error reports]
    end

    subgraph Integration
        RS[Reasoning Engine]
        PL[Planning Engine]
        DE[Decision Engine]
        WE[Workflow Engine]
        ME[Memory Engine]
        TF[Tool Framework]
        AR[Agent Registry]
        OR[Orchestrator]
    end

    LE --> LP
    LP --> FC --> ES
    LP --> PA --> RE
    LE --> LM
    Feedback Sources --> FC
    LE -.-> Integration
```

---

## Core Components

| Component | Role |
|-----------|------|
| `LearningEngine` | Central learning entry point |
| `LearningContext` | Feedback + execution history input |
| `LearningSession` | Active/completed learning cycle |
| `LearningRecord` | Stored pattern/outcome record |
| `LearningEvent` | Domain learning event |
| `FeedbackRecord` | Structured feedback with sentiment |
| `FeedbackCollector` | Multi-source feedback ingestion |
| `ExperienceStore` | Cross-layer execution history |
| `PatternAnalyzer` | Success/failure pattern detection |
| `RecommendationEngine` | Improvement recommendations |
| `LearningMetrics` | Cycle and improvement metrics |

---

## Feedback Model

| Field | Description |
|-------|-------------|
| Sentiment | `positive` · `neutral` · `negative` |
| Confidence score | 0–100 |
| Severity | 0 (low) – 100 (high) |
| Priority | Business priority weight |
| Category | workflow · planning · decision · reasoning · tool · agent · general |
| Source | workflow_result · task_result · human_feedback · agent_self_evaluation · tool_execution · system_event · error_report |
| Timestamp | Collection time |
| Message | Human-readable description |

---

## Learning Pipeline

1. Collect execution history (workflows, decisions, planning, reasoning, tools)
2. Collect feedback from all sources
3. Analyze outcomes
4. Detect successful patterns
5. Detect failure patterns
6. Generate recommendations
7. Store learning records
8. Expose learning insights

---

## Experience Store

Tracks history across platform layers:

- Successful / failed workflows
- Decision history
- Planning history
- Reasoning history
- Tool usage history
- Agent performance history
- Task results

---

## Recommendation Types

| Type | Description |
|------|-------------|
| Planning strategy | Suggest better planning approach |
| Decision policy | Suggest risk/cost/speed policy changes |
| Tool | Prefer or avoid specific tools |
| Agent | Prefer or review specific agents |
| Workflow optimization | Template successes or fix dependencies |
| Repeated failure | Alert on recurring error patterns |

---

## Usage

### Collect feedback

```python
from platform_learning import learning_engine, FeedbackSentiment

await learning_engine.collect_feedback(
    learning_engine._integrations.feedback_from_workflow("wf_123", success=True, agent_id="auto_agent")
)

from platform_learning.feedback_collector import feedback_collector

feedback_collector.collect_human_feedback(
    "Response was helpful",
    sentiment=FeedbackSentiment.POSITIVE,
    agent_id="auto_agent",
)
```

### Run learning cycle

```python
from platform_learning import LearningContext, learning_engine

ctx = LearningContext(
    agent_id="auto_agent",
    feedback=[...],
    execution_history={"workflows": [{"workflow_id": "w1", "success": True}]},
)
result = await learning_engine.learn(ctx)

for rec in result.recommendations:
    print(rec.title, rec.suggested_value)

engine.accept_recommendation(result.recommendations[0].recommendation_id)
```

### Agent-integrated learning

```python
result = await learning_engine.learn_for_agent("auto_agent", user_id="user_1")
print(result.insights)
```

---

## Integration Bridges

| Layer | Bridge |
|-------|--------|
| Reasoning | Aggregate reasoning metrics → history |
| Planning | Aggregate planning metrics → history |
| Decision | Aggregate decision metrics + feedback_from_decision |
| Workflow | Aggregate workflow metrics → history |
| Memory | enrich_with_memory via ContextAssembler |
| Tools | Tool metrics → history |
| Agents | agent_registry_feedback |
| Orchestrator | orchestrator_insights |

---

## Metrics

`learning_engine.metrics_summary()` returns:

| Metric | Description |
|--------|-------------|
| `learning_cycles` | Total cycles completed |
| `recommendation_acceptance_rate` | Accepted vs rejected recommendations |
| `pattern_detection_rate` | Patterns per cycle |
| `agent_improvement_score` | Rolling agent success score |
| `workflow_improvement_score` | Workflow success ratio |
| `feedback_volume` | Total feedback collected |

---

## Events

| Event | When |
|-------|------|
| `LearningCycleStartedEvent` | Learning cycle begins |
| `LearningCycleCompletedEvent` | Cycle finished with insights |
| `FeedbackReceivedEvent` | Feedback collected |
| `RecommendationGeneratedEvent` | Recommendation produced |
| `LearningFailedEvent` | Cycle error |

---

## Developer Guide

1. Collect feedback continuously via `FeedbackCollector` or `learning_engine.collect_feedback()`
2. Pass execution history or use `learn_for_agent()` for platform aggregation
3. Run `learning_engine.learn()` on a schedule or after workflow completion
4. Review `result.recommendations` and accept/reject to track acceptance rate
5. Apply suggested planning strategies, decision policies, or tool preferences
6. Inspect `result.success_patterns` / `failure_patterns` for audit

Package location: `platform_learning/`

Tests: `tests/test_learning_engine.py`
