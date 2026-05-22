# Autonomous Incident Response Engineer (AIRE)
### A Complete Learning & Build Guide

> *"What if your on-call rotation was an AI that never sleeps, never panics, and learns from every outage?"*

---

## Table of Contents

1. [What You're Building](#1-what-youre-building)
2. [The Mental Model — How to Think About This](#2-the-mental-model)
3. [Core Concepts You Must Master First](#3-core-concepts-you-must-master-first)
4. [System Architecture — The Full Picture](#4-system-architecture)
5. [Agent Design — Deep Dive](#5-agent-design)
6. [Data Flow & Orchestration](#6-data-flow--orchestration)
7. [The Tech Stack — Every Tool Explained](#7-the-tech-stack)
8. [Phase-by-Phase Build Plan](#8-phase-by-phase-build-plan)
9. [Phase 1 — Foundation (Weeks 1–3)](#9-phase-1--foundation)
10. [Phase 2 — Core Agents (Weeks 4–7)](#10-phase-2--core-agents)
11. [Phase 3 — Intelligence Layer (Weeks 8–11)](#11-phase-3--intelligence-layer)
12. [Phase 4 — Execution & Safety (Weeks 12–15)](#12-phase-4--execution--safety)
13. [Phase 5 — Frontend & Polish (Weeks 16–18)](#13-phase-5--frontend--polish)
14. [Real Incident Walkthroughs](#14-real-incident-walkthroughs)
15. [Security & Safety Model](#15-security--safety-model)
16. [Testing Strategy](#16-testing-strategy)
17. [Production Deployment](#17-production-deployment)
18. [What You'll Learn — Mapped to the Industry](#18-what-youll-learn)
19. [Career & Business Path](#19-career--business-path)
20. [Resources & References](#20-resources--references)

---

## 1. What You're Building

AIRE is a **multi-agent AI system** that acts as an autonomous Site Reliability Engineer. When something breaks in production, it:

```
Production Alert Fires
        │
        ▼
┌─────────────────┐
│  Observer Agent │  ← Detects anomaly from Prometheus/Loki/K8s events
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  Investigator Agent │  ← Queries logs, traces, git, deploys
└────────┬────────────┘
         │
         ▼
┌──────────────────────┐
│  Hypothesis Agent    │  ← Ranks root causes with confidence scores
└────────┬─────────────┘
         │
      ┌──┴───────────────┐
      ▼                  ▼
┌──────────┐      ┌────────────┐
│ Executor │      │   Report   │
│  Agent   │      │   Agent    │
│(optional)│      │(always on) │
└──────────┘      └────────────┘
   Fixes it        Writes postmortem
```

This is **not** a chatbot that helps you debug. It is an **autonomous loop** that detects, reasons, acts, and documents — without you being involved unless it can't figure something out.

---

## 2. The Mental Model

### Think of it as a hospital emergency room

| Hospital | AIRE |
|----------|------|
| Triage nurse | Observer Agent |
| ER Doctor | Investigator Agent |
| Differential diagnosis | Hypothesis Agent |
| Surgeon / pharmacist | Executor Agent |
| Medical records | Report Agent |
| Hospital administrator | Orchestrator |

Just like an ER, agents **work in parallel**, consult each other, and escalate when uncertain.

### The key insight: Agents are LLMs + Tools + Memory + Goals

An agent is not magic. It is:

```python
while not resolved:
    observation = tools.gather_context()
    thought = llm.reason(observation, memory, goal)
    action = llm.choose_action(thought, available_tools)
    result = tools.execute(action)
    memory.update(result)
    if llm.is_resolved(result):
        break
```

That loop, repeated across 5 specialized agents, is your entire system. Everything else is scaffolding around this core.

---

## 3. Core Concepts You Must Master First

Before writing a single line of agent code, understand these deeply. Each one is a 1–2 day study session.

### 3.1 Observability — The Three Pillars

**Logs** — What happened, as text
```
[2024-01-15 14:32:01] ERROR  app.db: Connection pool exhausted (pool_size=10, overflow=5)
[2024-01-15 14:32:01] ERROR  app.api: Request failed: /api/users — 503 Service Unavailable
```
Logs answer: *What error occurred?*

**Metrics** — What happened, as numbers over time
```
http_request_duration_seconds{method="GET", status="503"} 12.4
db_pool_connections_active 15
db_pool_connections_idle 0
```
Metrics answer: *How bad is it, and when did it start?*

**Traces** — How a single request traveled through your system
```
Trace: a1b2c3d4
  └─ API Gateway (12ms)
       └─ User Service (3ms)
            └─ Database Query (11,823ms) ← HERE IS THE PROBLEM
```
Traces answer: *Where exactly is the bottleneck in this specific request?*

> Your Observer Agent consumes all three. Your Investigator Agent correlates them.

### 3.2 Kubernetes Fundamentals

You need to understand these K8s objects because your Executor Agent will manipulate them:

```
Cluster
  └── Namespace (logical isolation)
       ├── Deployment (desired state: "run 3 copies of this app")
       │    └── ReplicaSet (manages the copies)
       │         └── Pod (one instance of your app)
       │              └── Container (the actual process)
       ├── Service (load balancer / DNS for pods)
       ├── ConfigMap (environment config)
       └── HPA (HorizontalPodAutoscaler — auto-scales pods)
```

Key commands your Executor Agent wraps:
```bash
kubectl get pods -n production              # list pods
kubectl logs pod-name --previous            # logs from crashed pod
kubectl describe pod pod-name              # full pod status
kubectl rollout undo deployment/app-name   # rollback
kubectl scale deployment app --replicas=5  # scale up
kubectl top pods                           # CPU/memory usage
```

### 3.3 How LLM Tool Calling Works

This is the mechanical foundation of every agent:

```python
# You give the LLM a list of tools it CAN call
tools = [
    {
        "name": "query_prometheus",
        "description": "Query Prometheus metrics. Use for CPU, memory, request rates.",
        "parameters": {
            "query": "PromQL query string",
            "time_range": "e.g. '30m', '1h', '24h'"
        }
    },
    {
        "name": "search_logs",
        "description": "Search Loki logs. Use for error messages, stack traces.",
        "parameters": {
            "query": "LogQL query string",
            "limit": "max results to return"
        }
    }
]

# The LLM decides WHAT to call and WITH WHAT arguments
response = llm.complete(
    messages=[{"role": "user", "content": "CPU is spiking on pod api-7f8b9. Investigate."}],
    tools=tools
)

# response.tool_calls = [
#   {"name": "query_prometheus", "args": {"query": "rate(cpu_usage[5m]){pod='api-7f8b9'}", "time_range": "1h"}},
#   {"name": "search_logs", "args": {"query": "{pod='api-7f8b9'} |= 'ERROR'", "limit": "100"}}
# ]
```

The LLM is the **brain**. The tools are the **hands**. Your orchestrator connects them.

### 3.4 Event-Driven Architecture

Your system communicates through events, not direct function calls:

```
[Alert Fires] → Redis Stream: "incidents" → Observer picks it up
                                           → Observer emits: "incident.detected"
                                           → Investigator picks it up
                                           → Investigator emits: "incident.investigated"
                                           → Hypothesis Agent picks it up
                                           → ... and so on
```

Why events instead of direct calls?
- **Resilience**: If one agent crashes, the event stays in the stream
- **Parallelism**: Multiple agents can process different events simultaneously
- **Replay**: You can replay events for debugging or training
- **Audit trail**: Every action is logged as an event

### 3.5 Memory in AI Agents

Agents need four types of memory:

```
┌──────────────────────────────────────────────────────┐
│                    Agent Memory                       │
│                                                      │
│  In-Context  │ Working memory. The current LLM prompt │
│  (short-term)│ Max ~128k tokens. Lost after session.  │
│              │                                        │
│  Episodic    │ "Last time this alert fired, it was   │
│  (incidents) │ caused by a bad deploy. Confidence: 87%│
│              │                                        │
│  Semantic    │ Embeddings of runbooks, past RCAs,    │
│  (knowledge) │ architecture docs. Retrieved via RAG.  │
│              │                                        │
│  Procedural  │ Which tools to call for which kind    │
│  (skills)    │ of incident. Encoded in the prompt.   │
└──────────────────────────────────────────────────────┘
```

Your system uses **PostgreSQL + pgvector** for episodic and semantic memory, and **Redis** for fast short-term state.

---

## 4. System Architecture — The Full Picture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AIRE System                                  │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   Frontend  │    │  REST API   │    │     WebSocket Gateway   │ │
│  │  (Next.js)  │◄──►│  (FastAPI)  │◄──►│  (realtime events)      │ │
│  └─────────────┘    └──────┬──────┘    └────────────┬────────────┘ │
│                            │                         │              │
│  ┌─────────────────────────▼─────────────────────────▼───────────┐ │
│  │                    Orchestrator                                │ │
│  │              (LangGraph / Custom State Machine)                │ │
│  └──────────────┬──────────────────────────────────┬─────────────┘ │
│                 │                                  │               │
│  ┌──────────────▼──────────────────────────────────▼────────────┐  │
│  │                     Redis Streams                             │  │
│  │         (incident.detected → investigated → resolved)        │  │
│  └──────────────┬──────────────────────────────────┬────────────┘  │
│                 │                                  │               │
│    ┌────────────▼──────┐              ┌────────────▼──────────┐    │
│    │   Agent Workers   │              │   Tool Integrations   │    │
│    │                   │              │                       │    │
│    │  ┌─────────────┐  │              │  ┌─────────────────┐  │    │
│    │  │  Observer   │  │◄────────────►│  │   Prometheus    │  │    │
│    │  └─────────────┘  │              │  └─────────────────┘  │    │
│    │  ┌─────────────┐  │              │  ┌─────────────────┐  │    │
│    │  │Investigator │  │◄────────────►│  │      Loki       │  │    │
│    │  └─────────────┘  │              │  └─────────────────┘  │    │
│    │  ┌─────────────┐  │              │  ┌─────────────────┐  │    │
│    │  │ Hypothesis  │  │◄────────────►│  │   Kubernetes    │  │    │
│    │  └─────────────┘  │              │  └─────────────────┘  │    │
│    │  ┌─────────────┐  │              │  ┌─────────────────┐  │    │
│    │  │  Executor   │  │◄────────────►│  │    GitHub API   │  │    │
│    │  └─────────────┘  │              │  └─────────────────┘  │    │
│    │  ┌─────────────┐  │              │  ┌─────────────────┐  │    │
│    │  │   Report    │  │◄────────────►│  │  Slack / Jira   │  │    │
│    │  └─────────────┘  │              │  └─────────────────┘  │    │
│    └───────────────────┘              └───────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      Data Layer                               │  │
│  │   PostgreSQL (incidents, RCAs, audit log, agent reasoning)   │  │
│  │   pgvector (embeddings of runbooks, past incidents)          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Agent Design — Deep Dive

### 5.1 Observer Agent

**Purpose**: Continuously polls data sources, detects anomalies, fires incidents.

**How it detects anomalies**:
```python
class ObserverAgent:
    async def check_prometheus(self):
        # Static threshold check
        error_rate = await prometheus.query(
            'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))'
        )
        if error_rate > 0.05:  # 5% error rate threshold
            await self.fire_incident("High error rate", severity="HIGH", value=error_rate)

        # Dynamic anomaly detection (z-score)
        current = await prometheus.query('rate(http_requests_total[5m])')
        baseline = await prometheus.query_range('rate(http_requests_total[5m])', range='7d')
        zscore = (current - mean(baseline)) / std(baseline)
        if abs(zscore) > 3:  # 3 standard deviations from normal
            await self.fire_incident("Traffic anomaly", severity="MEDIUM", zscore=zscore)
```

**What it monitors**:
- Prometheus alert rules (when Alertmanager webhooks fire)
- Kubernetes events (`kubectl get events --watch`)
- Log error rates (Loki)
- Custom business metrics (orders per minute, auth failure rates)
- AWS CloudWatch alarms
- PagerDuty webhook ingestion

**Output event**:
```json
{
  "incident_id": "inc-2024-001",
  "type": "error_rate_spike",
  "severity": "HIGH",
  "started_at": "2024-01-15T14:30:00Z",
  "affected_services": ["api-gateway", "user-service"],
  "initial_signals": {
    "error_rate": 0.34,
    "p99_latency_ms": 12400,
    "active_pods": 3,
    "expected_pods": 5
  },
  "raw_alerts": [...]
}
```

---

### 5.2 Investigator Agent

**Purpose**: Builds a complete causal timeline of what happened and when.

**This is the most technically complex agent.** It must:
1. Query logs during the incident window
2. Query metrics before/during/after
3. Look at deployment history (git, Argo CD, Helm)
4. Check infrastructure changes (Terraform, AWS console)
5. Look at recent K8s events
6. Correlate everything into a timeline

**System prompt (critical — this shapes all reasoning)**:
```
You are a senior SRE investigating a production incident.
Your job is to build a CAUSAL TIMELINE — not just a list of events,
but a chain showing cause → effect → cause → effect.

Available tools: query_logs, query_metrics, get_deployments,
                 get_k8s_events, get_git_commits, query_traces

Process:
1. Establish the BASELINE — what does normal look like?
2. Find the FIRST DEVIATION — when did metrics first leave normal?
3. Work BACKWARDS from the alert — what changed before the deviation?
4. Correlate ACROSS SERVICES — did this spread? How?
5. Find the TRIGGER — the root action that started everything.

Always cite specific log lines, metric values, and timestamps.
Format your output as a timeline with confidence scores.
```

**Example output**:
```json
{
  "timeline": [
    {
      "time": "14:27:32",
      "event": "Deployment api-gateway v1.4.2 rolled out",
      "source": "argocd",
      "confidence": 1.0
    },
    {
      "time": "14:28:01",
      "event": "DB connection pool began growing (8/10 active)",
      "source": "prometheus",
      "confidence": 0.95
    },
    {
      "time": "14:29:15",
      "event": "First 503 errors appeared in API gateway logs",
      "source": "loki",
      "confidence": 1.0,
      "evidence": "14:29:15 ERROR Connection pool exhausted pool_size=10"
    },
    {
      "time": "14:30:00",
      "event": "PagerDuty alert fired",
      "source": "pagerduty",
      "confidence": 1.0
    }
  ],
  "causal_chain": "Deploy v1.4.2 introduced unbounded DB query → pool exhausted → 503s",
  "time_to_impact_seconds": 148
}
```

---

### 5.3 Hypothesis Agent

**Purpose**: Generate ranked root cause hypotheses with confidence scores.

**This is where RAG comes in.** Before generating hypotheses, it retrieves:
- Similar past incidents from the vector database
- Relevant runbooks
- Architecture documentation

```python
class HypothesisAgent:
    async def generate(self, incident: Incident, investigation: Investigation) -> List[Hypothesis]:
        # RAG: find similar past incidents
        similar_incidents = await self.vector_db.similarity_search(
            query=f"{incident.type} {incident.affected_services}",
            k=5,
            filter={"resolved": True}
        )

        # Build context-rich prompt
        prompt = f"""
        Current incident: {incident.model_dump_json()}
        Investigation findings: {investigation.timeline}

        Similar past incidents and their root causes:
        {format_similar_incidents(similar_incidents)}

        Generate the top 5 most likely root causes.
        For each hypothesis:
        - State the root cause clearly
        - Explain the causal mechanism
        - List the evidence that supports it
        - List evidence that contradicts it
        - Assign a confidence score (0.0 - 1.0)
        - Suggest one diagnostic action to confirm or reject it
        """

        response = await self.llm.complete(prompt)
        return self.parse_hypotheses(response)
```

**Example output**:
```
HYPOTHESIS RANKING

1. DB Connection Pool Exhaustion (confidence: 0.91)
   Cause: New deployment v1.4.2 added N+1 query in user authentication,
          opening 5 connections per request instead of 1.
   Evidence for: Pool at 100%, timing matches deploy, logs show pool errors
   Evidence against: No change in DB CPU, only specific endpoint affected
   Next step: Compare auth query count per request in v1.4.1 vs v1.4.2

2. Memory Leak in New Build (confidence: 0.43)
   Cause: Memory pressure forcing GC pauses, causing timeouts
   Evidence for: Memory trending up after deploy
   Evidence against: Pool errors are explicit, GC is not in logs
   Next step: Compare heap dumps from v1.4.1 and v1.4.2 pods

3. External Database Slowdown (confidence: 0.21)
   Cause: RDS instance hitting IOPS limit
   Evidence for: High latency on DB queries
   Evidence against: Other services using same DB are fine
   Next step: Check CloudWatch RDS IOPS metrics
```

---

### 5.4 Executor Agent

**Purpose**: Take remediation actions — safely, with human approval gates.

**This is the most dangerous agent.** You must design it with extreme care.

**Safety model: Action tiers**

```python
class ActionTier(Enum):
    SAFE = "safe"           # Always execute automatically
    CAUTIOUS = "cautious"   # Execute after 60-second timeout (allows human cancel)
    DANGEROUS = "dangerous" # Requires explicit human approval
    FORBIDDEN = "forbidden" # Never execute, ever

ACTION_TIERS = {
    # SAFE — low blast radius, easily reversible
    "scale_up_replicas": ActionTier.SAFE,
    "create_jira_ticket": ActionTier.SAFE,
    "send_slack_notification": ActionTier.SAFE,

    # CAUTIOUS — moderate blast radius, reversible
    "restart_single_pod": ActionTier.CAUTIOUS,
    "rollback_deployment": ActionTier.CAUTIOUS,
    "block_ip_address": ActionTier.CAUTIOUS,

    # DANGEROUS — high blast radius or hard to reverse
    "delete_namespace": ActionTier.DANGEROUS,
    "rotate_production_secrets": ActionTier.DANGEROUS,
    "modify_database_schema": ActionTier.DANGEROUS,

    # FORBIDDEN — never let AI do this
    "drop_database": ActionTier.FORBIDDEN,
    "delete_s3_bucket": ActionTier.FORBIDDEN,
    "terminate_all_instances": ActionTier.FORBIDDEN,
}
```

**Executor tool implementations**:
```python
async def rollback_deployment(self, namespace: str, deployment: str) -> ActionResult:
    """Roll back a Kubernetes deployment to the previous revision."""
    # 1. Dry run first
    dry_run = await kubectl.run(
        f"rollout undo deployment/{deployment} -n {namespace} --dry-run=client"
    )
    if dry_run.returncode != 0:
        return ActionResult(success=False, error=dry_run.stderr)

    # 2. Get current revision for rollback tracking
    history = await kubectl.run(
        f"rollout history deployment/{deployment} -n {namespace}"
    )

    # 3. Execute actual rollback
    result = await kubectl.run(
        f"rollout undo deployment/{deployment} -n {namespace}"
    )

    # 4. Wait for rollout and verify
    await kubectl.run(
        f"rollout status deployment/{deployment} -n {namespace} --timeout=120s"
    )

    return ActionResult(
        success=True,
        action="rollback_deployment",
        details={"namespace": namespace, "deployment": deployment},
        reversible=False,  # rolled back once, can't easily re-forward
        audit_log=result.stdout
    )
```

---

### 5.5 Report Agent

**Purpose**: Generate incident timelines, RCA documents, Slack summaries, and leadership reports.

**This is the output the business sees.** It must be:
- Accurate (pulled from structured incident data, not hallucinated)
- Appropriate for the audience (engineers vs. leadership vs. customers)
- Actionable (what must change to prevent recurrence)

```python
class ReportAgent:
    async def generate_postmortem(self, incident: FullIncidentRecord) -> Postmortem:
        # Each section gets its own LLM call with relevant context
        # This prevents context overflow and keeps each section focused

        summary = await self.llm.complete(
            f"Write a 3-sentence executive summary of this incident: {incident.summary}"
        )

        timeline = await self.format_timeline(incident.investigation.timeline)

        root_cause = await self.llm.complete(
            f"""
            Write a clear root cause analysis section.
            Confirmed root cause: {incident.hypothesis.top_hypothesis}
            Evidence: {incident.investigation.evidence}
            Do NOT speculate. Only state confirmed facts.
            """
        )

        action_items = await self.llm.complete(
            f"""
            Generate specific, measurable action items to prevent recurrence.
            Each action item must have:
            - Owner team (e.g. "Platform Engineering")
            - Deadline (e.g. "2 weeks", "next sprint")
            - Success criterion
            Root cause: {incident.hypothesis.top_hypothesis}
            """
        )

        return Postmortem(
            summary=summary,
            timeline=timeline,
            impact=incident.impact,
            root_cause=root_cause,
            action_items=action_items,
            generated_at=datetime.utcnow()
        )
```

---

## 6. Data Flow & Orchestration

### The Incident Lifecycle as a State Machine

```
[IDLE]
   │
   │ Alert fires / anomaly detected
   ▼
[DETECTING]  ← Observer Agent active
   │
   │ Incident created with severity and signals
   ▼
[INVESTIGATING]  ← Investigator Agent active
   │
   │ Timeline and evidence collected
   ▼
[HYPOTHESIZING]  ← Hypothesis Agent active
   │
   │ Root causes ranked with confidence
   ├──────────────────────────────────────┐
   │ High confidence (>0.8) + SAFE action │ Medium/low confidence or DANGEROUS
   ▼                                      ▼
[EXECUTING_AUTO]                    [AWAITING_HUMAN]
   │                                      │
   │                                 Human approves
   ▼                                      ▼
[REMEDIATING]  ← Executor Agent active
   │
   │ Actions taken
   ▼
[REPORTING]  ← Report Agent active (always runs)
   │
   ▼
[RESOLVED]  → Incident stored → Embeddings updated for future RAG
```

### Implementing with LangGraph

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

class IncidentState(TypedDict):
    incident_id: str
    severity: str
    signals: dict
    timeline: list
    hypotheses: list
    approved_actions: list
    actions_taken: list
    postmortem: str
    human_approval_needed: bool

def build_incident_graph():
    graph = StateGraph(IncidentState)

    # Add nodes (each is an agent or checkpoint)
    graph.add_node("observe", observer_agent.run)
    graph.add_node("investigate", investigator_agent.run)
    graph.add_node("hypothesize", hypothesis_agent.run)
    graph.add_node("check_approval", check_if_human_approval_needed)
    graph.add_node("human_approval", HumanApprovalNode())  # pauses here
    graph.add_node("execute", executor_agent.run)
    graph.add_node("report", report_agent.run)

    # Define edges
    graph.add_edge("observe", "investigate")
    graph.add_edge("investigate", "hypothesize")
    graph.add_edge("hypothesize", "check_approval")
    graph.add_conditional_edges(
        "check_approval",
        lambda state: "human_approval" if state["human_approval_needed"] else "execute"
    )
    graph.add_edge("human_approval", "execute")
    graph.add_edge("execute", "report")
    graph.add_edge("report", END)

    graph.set_entry_point("observe")

    # Enable checkpointing so the graph survives crashes
    return graph.compile(checkpointer=MemorySaver())
```

---

## 7. The Tech Stack — Every Tool Explained

### Why Each Tool?

| Tool | What it Does | Why You're Using It |
|------|-------------|---------------------|
| **FastAPI** | HTTP API framework | Async-native, auto OpenAPI docs, fast |
| **LangGraph** | Agent orchestration | Manages agent state, loops, human-in-the-loop |
| **Redis Streams** | Event queue | Low latency, persistent, consumer groups |
| **PostgreSQL** | Primary database | ACID, excellent Python support, pgvector addon |
| **pgvector** | Vector search | RAG for past incidents and runbooks |
| **Prometheus** | Metrics collection | Industry standard, powerful PromQL |
| **Loki** | Log aggregation | Prometheus-native, LogQL similar to PromQL |
| **Grafana** | Dashboards | Visualize metrics and logs in one place |
| **k3s** | Lightweight K8s | Run Kubernetes locally for dev/testing |
| **Docker** | Container runtime | Package and run everything consistently |
| **OpenAI / Gemini** | LLM backend | Main reasoning engine for all agents |
| **Next.js** | Frontend | React with SSR, excellent real-time support |

### How Prometheus Works (under the hood)

```yaml
# prometheus.yml — tells Prometheus what to scrape
scrape_configs:
  - job_name: 'api-service'
    static_configs:
      - targets: ['api-service:8080']
    # Prometheus calls GET /metrics on this every 15s
    # Your app exposes metrics there
```

Your app exposes:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 10234
http_requests_total{method="GET",status="503"} 847

# HELP http_request_duration_seconds Request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 9500
http_request_duration_seconds_bucket{le="1.0"} 10100
http_request_duration_seconds_bucket{le="+Inf"} 10234
```

Your agent queries Prometheus:
```python
async def query_prometheus(self, query: str, time_range: str = "5m") -> dict:
    response = await httpx.get(
        f"{self.prometheus_url}/api/v1/query",
        params={"query": query, "time": int(time.time())}
    )
    return response.json()

# Example: "What's the error rate right now?"
result = await query_prometheus(
    'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))'
)
```

### How Loki Works

Loki stores logs indexed by **labels**, not full-text.

```python
async def search_logs(self, service: str, level: str, query: str, time_range: str) -> list:
    # LogQL query
    logql = f'{{service="{service}", level="{level}"}} |= "{query}"'

    response = await httpx.get(
        f"{self.loki_url}/loki/api/v1/query_range",
        params={
            "query": logql,
            "start": int((datetime.utcnow() - parse_duration(time_range)).timestamp() * 1e9),
            "end": int(datetime.utcnow().timestamp() * 1e9),
            "limit": 1000
        }
    )
    return self.parse_loki_response(response.json())
```

---

## 8. Phase-by-Phase Build Plan

### Overview

| Phase | Duration | What You Build | Key Skill Gained |
|-------|----------|----------------|------------------|
| 1 — Foundation | 3 weeks | Infrastructure, data models, event bus | DevOps fundamentals |
| 2 — Core Agents | 4 weeks | All 5 agents (no execution yet) | Agent engineering |
| 3 — Intelligence | 4 weeks | RAG, memory, confidence scoring | ML engineering |
| 4 — Execution | 4 weeks | Executor + safety system | Systems security |
| 5 — Frontend | 3 weeks | Realtime UI, topology maps | Full-stack |

**Total: ~18 weeks** for a production-ready system. But you have something demo-able by **week 7**.

---

## 9. Phase 1 — Foundation

### Week 1: Local Infrastructure

Set up your complete observability stack locally.

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  # Observability Stack
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
    ports:
      - "3000:3000"

  # AIRE Backend Services
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: aire
      POSTGRES_USER: aire
      POSTGRES_PASSWORD: aire_dev
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Sample broken application (for testing)
  sample-api:
    build: ./sample-apps/api
    environment:
      - DB_URL=postgresql://aire:aire_dev@postgres/sample
    ports:
      - "8001:8000"
```

**Install k3s locally**:
```bash
curl -sfL https://get.k3s.io | sh -
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl get nodes  # Should show 1 node
```

**Goals by end of Week 1**:
- Grafana showing dashboards at localhost:3000
- Prometheus scraping metrics
- PostgreSQL running with pgvector extension
- Redis running
- k3s cluster with a sample app deployed

---

### Week 2: Data Models & Event Bus

**Incident data models** (`models/incident.py`):
```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IncidentStatus(str, Enum):
    DETECTING = "detecting"
    INVESTIGATING = "investigating"
    HYPOTHESIZING = "hypothesizing"
    AWAITING_APPROVAL = "awaiting_approval"
    REMEDIATING = "remediating"
    REPORTING = "reporting"
    RESOLVED = "resolved"

class Incident(BaseModel):
    id: str
    title: str
    severity: Severity
    status: IncidentStatus
    affected_services: list[str]
    started_at: datetime
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    # Signal data
    initial_signals: dict
    error_rate: Optional[float] = None
    p99_latency_ms: Optional[float] = None

class Investigation(BaseModel):
    incident_id: str
    timeline: list[TimelineEvent]
    causal_chain: str
    evidence: list[Evidence]
    queries_executed: list[str]
    agent_reasoning: str

class Hypothesis(BaseModel):
    incident_id: str
    rank: int
    root_cause: str
    mechanism: str
    evidence_for: list[str]
    evidence_against: list[str]
    confidence: float  # 0.0 - 1.0
    next_diagnostic: str
```

**Redis Streams event bus**:
```python
import redis.asyncio as redis
import json

class EventBus:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.streams = {
            "incidents": "aire:incidents",
            "investigations": "aire:investigations",
            "hypotheses": "aire:hypotheses",
            "actions": "aire:actions"
        }

    async def publish(self, stream: str, event: dict) -> str:
        """Publish an event to a stream. Returns message ID."""
        message_id = await self.redis.xadd(
            self.streams[stream],
            {"data": json.dumps(event), "timestamp": datetime.utcnow().isoformat()}
        )
        return message_id

    async def subscribe(self, stream: str, consumer_group: str, consumer_name: str):
        """Subscribe to a stream as part of a consumer group."""
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(self.streams[stream], consumer_group, id="0")
        except redis.ResponseError:
            pass  # Group already exists

        while True:
            messages = await self.redis.xreadgroup(
                consumer_group, consumer_name,
                {self.streams[stream]: ">"},
                count=1, block=1000
            )
            if messages:
                for _, message_list in messages:
                    for message_id, fields in message_list:
                        yield json.loads(fields[b"data"])
                        await self.redis.xack(self.streams[stream], consumer_group, message_id)
```

---

### Week 3: Tool Integrations

Build the tool layer that all agents will use:

```python
# tools/prometheus_tool.py
class PrometheusTools:
    BASE_QUERIES = {
        "error_rate": 'sum(rate(http_requests_total{{status=~"5.."}}[{range}])) / sum(rate(http_requests_total[{range}]))',
        "latency_p99": 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[{range}])) by (le, service))',
        "cpu_usage": 'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[{range}])) by (pod)',
        "memory_usage": 'sum(container_memory_working_set_bytes{{namespace="{namespace}"}}) by (pod)',
        "pod_restarts": 'increase(kube_pod_container_status_restarts_total{{namespace="{namespace}"}}[{range}])',
    }

    async def get_error_rate(self, service: str, time_range: str = "5m") -> float:
        query = self.BASE_QUERIES["error_rate"].format(range=time_range)
        result = await self._query(query)
        return float(result["data"]["result"][0]["value"][1]) if result["data"]["result"] else 0.0

    async def get_metric_history(self, metric: str, hours: int = 24) -> list:
        """Get metric values over time for baseline comparison."""
        end = int(time.time())
        start = end - (hours * 3600)
        response = await httpx.get(
            f"{self.base_url}/api/v1/query_range",
            params={"query": metric, "start": start, "end": end, "step": "60"}
        )
        return response.json()["data"]["result"]
```

---

## 10. Phase 2 — Core Agents

### Week 4: Observer Agent

```python
class ObserverAgent:
    def __init__(self, tools: ToolRegistry, event_bus: EventBus, llm: LLM):
        self.tools = tools
        self.event_bus = event_bus
        self.llm = llm
        self.polling_interval = 30  # seconds

    async def run(self):
        """Main loop — runs forever."""
        while True:
            try:
                await self.check_all_sources()
            except Exception as e:
                logger.error(f"Observer error: {e}")
            await asyncio.sleep(self.polling_interval)

    async def check_all_sources(self):
        # Run all checks in parallel
        results = await asyncio.gather(
            self.check_prometheus_alerts(),
            self.check_kubernetes_events(),
            self.check_log_error_rates(),
            return_exceptions=True
        )
        for anomaly in filter(None, results):
            if isinstance(anomaly, Exception):
                continue
            await self.create_incident(anomaly)

    async def check_prometheus_alerts(self) -> Optional[AnomalySignal]:
        alerts = await self.tools.prometheus.get_firing_alerts()
        if alerts:
            return AnomalySignal(
                type="prometheus_alert",
                severity=self.map_alert_severity(alerts[0]),
                services=self.extract_affected_services(alerts),
                signals={"alerts": [a.dict() for a in alerts]}
            )
        return None
```

### Week 5: Investigator Agent

The investigator is a **ReAct agent** (Reason + Act loop):

```python
INVESTIGATOR_SYSTEM_PROMPT = """
You are investigating a production incident. Use your tools to build a complete
causal timeline. Think step by step:

1. FIRST: Understand what the alert says
2. SECOND: Query metrics to find when the deviation started
3. THIRD: Look for changes (deploys, config changes) before the deviation
4. FOURTH: Query logs during the incident window for error messages
5. FIFTH: Check if other services are affected (blast radius)
6. SIXTH: Build a causal chain: "X happened → which caused Y → which triggered Z"

Be systematic. Check one hypothesis at a time. Always include timestamps and values.
When you have enough evidence to explain the incident, call finish_investigation.
"""

class InvestigatorAgent:
    async def investigate(self, incident: Incident) -> Investigation:
        messages = [
            {"role": "system", "content": INVESTIGATOR_SYSTEM_PROMPT},
            {"role": "user", "content": f"""
                Incident: {incident.title}
                Severity: {incident.severity}
                Affected services: {incident.affected_services}
                Started: {incident.started_at}
                Initial signals: {json.dumps(incident.initial_signals, indent=2)}

                Begin investigation.
            """}
        ]

        # ReAct loop
        for _ in range(20):  # Max 20 tool calls
            response = await self.llm.complete(messages, tools=self.tools)

            if response.stop_reason == "end_turn":
                break

            if response.tool_calls:
                messages.append({"role": "assistant", "content": response.content})
                for tool_call in response.tool_calls:
                    result = await self.execute_tool(tool_call)
                    messages.append({"role": "tool", "content": result, "tool_use_id": tool_call.id})

        return self.parse_investigation(messages)
```

### Week 6: Hypothesis Agent

### Week 7: Report Agent (+ first demo!)

By end of week 7, you can demo:
- Inject a fake incident (kill a pod)
- Watch Observer detect it
- Watch Investigator query logs and metrics
- See Hypothesis Agent rank root causes
- See a postmortem automatically generated

---

## 11. Phase 3 — Intelligence Layer

### Week 8–9: RAG System for Historical Incidents

```python
# Set up pgvector
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE incident_embeddings (
    id UUID PRIMARY KEY,
    incident_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embedding dimension
    incident_type VARCHAR,
    root_cause VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON incident_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

```python
class IncidentMemory:
    async def store_resolved_incident(self, incident: FullIncidentRecord):
        """After resolving, embed and store for future RAG."""
        content = f"""
        Incident: {incident.title}
        Affected services: {', '.join(incident.affected_services)}
        Symptoms: {incident.investigation.causal_chain}
        Root cause: {incident.top_hypothesis.root_cause}
        Fix applied: {', '.join([a.description for a in incident.actions_taken])}
        Duration: {incident.duration_minutes} minutes
        """

        embedding = await self.openai.embed(content)

        await self.db.execute("""
            INSERT INTO incident_embeddings (id, incident_id, content, embedding, root_cause)
            VALUES ($1, $2, $3, $4, $5)
        """, uuid4(), incident.id, content, embedding, incident.top_hypothesis.root_cause)

    async def find_similar(self, query: str, k: int = 5) -> list[SimilarIncident]:
        """Find past incidents similar to the current one."""
        query_embedding = await self.openai.embed(query)

        results = await self.db.fetch("""
            SELECT incident_id, content, root_cause,
                   1 - (embedding <=> $1) as similarity
            FROM incident_embeddings
            ORDER BY embedding <=> $1
            LIMIT $2
        """, query_embedding, k)

        return [SimilarIncident(**r) for r in results]
```

### Week 10: Confidence Scoring System

```python
class ConfidenceScorer:
    """Calculates confidence scores for hypotheses using multiple signals."""

    def score(self, hypothesis: Hypothesis, investigation: Investigation) -> float:
        weights = {
            "evidence_count": 0.3,
            "temporal_correlation": 0.3,
            "similar_incidents": 0.2,
            "absence_of_contradictions": 0.2,
        }

        scores = {
            "evidence_count": self.score_evidence_count(hypothesis),
            "temporal_correlation": self.score_temporal_correlation(hypothesis, investigation),
            "similar_incidents": self.score_historical_match(hypothesis),
            "absence_of_contradictions": self.score_contradictions(hypothesis),
        }

        return sum(weight * scores[factor] for factor, weight in weights.items())
```

### Week 11: Runbook RAG + Agent Evaluation

Embed your runbooks and architecture docs for the agents to retrieve:
```python
# Embed all runbooks on startup
for runbook in glob.glob("./runbooks/**/*.md"):
    content = open(runbook).read()
    chunks = chunk_text(content, chunk_size=500, overlap=50)
    for chunk in chunks:
        embedding = await embed(chunk)
        await store_runbook_chunk(runbook_path=runbook, content=chunk, embedding=embedding)
```

---

## 12. Phase 4 — Execution & Safety

### Week 12–13: Executor Agent

**Permission model**:
```python
class ExecutorPermissions(BaseModel):
    allowed_namespaces: list[str] = ["production", "staging"]
    forbidden_namespaces: list[str] = ["kube-system", "monitoring"]
    max_replicas: int = 20
    require_human_above_severity: Severity = Severity.CRITICAL
    cooldown_seconds: int = 300  # Wait 5 min between same action
```

**Full audit trail**:
```python
async def execute_with_audit(self, action: Action, incident: Incident) -> ActionResult:
    # Record intent
    audit_id = await self.audit_log.record_intent(
        action=action,
        incident_id=incident.id,
        reasoning=action.reasoning,
        confidence=action.confidence
    )

    # Execute
    result = await self.execute(action)

    # Record outcome
    await self.audit_log.record_outcome(
        audit_id=audit_id,
        success=result.success,
        output=result.output,
        duration_ms=result.duration_ms
    )

    return result
```

### Week 14–15: Human-in-the-Loop

When the Executor needs approval, it pauses the LangGraph state and sends to frontend:

```python
class HumanApprovalNode:
    async def __call__(self, state: IncidentState) -> IncidentState:
        # Send approval request via WebSocket to frontend
        await self.ws_gateway.send(state["incident_id"], {
            "type": "approval_required",
            "actions": state["proposed_actions"],
            "hypothesis": state["top_hypothesis"],
            "confidence": state["confidence_score"],
            "timeout_seconds": 120
        })

        # Block until approved, rejected, or timeout
        approval = await self.wait_for_approval(
            incident_id=state["incident_id"],
            timeout=120
        )

        if approval.approved:
            state["approved_actions"] = approval.selected_actions
        else:
            state["approved_actions"] = []
            state["human_override"] = approval.override_action

        return state
```

---

## 13. Phase 5 — Frontend & Polish

### Week 16–18: Next.js Frontend

**Key views to build**:

1. **Incident Command Center** — Live feed of active incidents
2. **Agent Reasoning Timeline** — See each agent's thought process in real-time
3. **Hypothesis Confidence Dashboard** — Visual ranking of root causes
4. **Action Approval Panel** — Human approves/rejects executor actions
5. **Postmortem Viewer** — Read-only RCA documents
6. **System Topology Map** — D3 graph of services, highlighting affected nodes

**Real-time with WebSockets**:
```typescript
// hooks/useIncidentStream.ts
export function useIncidentStream(incidentId: string) {
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/incidents/${incidentId}`);

    ws.onmessage = (event) => {
      const agentEvent: AgentEvent = JSON.parse(event.data);
      setEvents(prev => [...prev, agentEvent]);
    };

    return () => ws.close();
  }, [incidentId]);

  return events;
}
```

---

## 14. Real Incident Walkthroughs

### Walkthrough 1: DB Connection Pool Exhaustion

**Setup** (you simulate this):
```bash
# Deploy a version of the app with N+1 query bug
kubectl set image deployment/api-gateway app=your-app:v-broken -n production

# Watch your system respond
```

**What AIRE does**:
```
14:27:32  Deploy api-gateway:v-broken completes

14:28:01  Observer: DB connection metric crosses 80% threshold
          → Fires incident INC-001 severity=HIGH

14:28:05  Investigator begins
          → Calls query_prometheus("db_pool_connections_active[1h]")
          → Calls search_logs("{service='api-gateway'}", level="ERROR", last="10m")
          → Finds: "14:27:45 ERROR Connection pool exhausted pool_size=10"
          → Calls get_deployments(namespace="production", last="30m")
          → Finds: api-gateway:v-broken deployed at 14:27:32
          → TIMELINE ESTABLISHED: Deploy → Pool exhaustion

14:28:47  Hypothesis Agent
          → Retrieves 3 similar past incidents (DB pool + deploy)
          → Hypothesis 1: "N+1 query in new version" confidence=0.87
          → Hypothesis 2: "Connection leak" confidence=0.34

14:29:01  Executor proposes:
          → rollback_deployment(api-gateway) [tier: CAUTIOUS]
          → Waits 60 seconds for human cancel

14:30:01  No cancel received → Rollback executes
          → kubectl rollout undo deployment/api-gateway

14:30:45  Metrics normalize. Error rate drops to 0%.

14:31:00  Report Agent generates postmortem
          → Root cause, timeline, action items
          → Posts to Slack #incidents
          → Creates Jira ticket PLAT-1234
          → Labels: "needs-n-plus-one-fix", "api-gateway", "database"

14:31:30  Incident RESOLVED
          → Stored in vector DB for future RAG
```

**Time to resolution: 4 minutes. On-call engineer did nothing.**

---

### Walkthrough 2: Memory Leak → OOM Kill Loop

**Signals**: K8s CrashLoopBackOff events, pod restart count increasing, OOMKilled exit code

**What AIRE does differently**:
```
Observer: K8s event watcher sees OOMKilled exit code
Investigator: Queries pod memory metrics over 6 hours → steady growth pattern
Hypothesis: Memory leak (confidence 0.79) vs. traffic spike (0.21)
Executor: Proposes scale_up_replicas (SAFE, buys time) + create_jira (code fix needed)
Report: "Immediate: scaled to 6 replicas. Root cause requires code fix. Ticket PLAT-1235."
```

Note: The executor does NOT fix the memory leak. It knows its limits. It buys time and escalates correctly.

---

## 15. Security & Safety Model

### The Three Laws of Your Executor

1. **Never delete data** — No DROP, no DELETE without human explicit approval, no S3 bucket deletion
2. **Prefer reversible actions** — Scale up before scaling down; rollback before deploying forward
3. **Fail open for safety** — If uncertain, do nothing and alert human

### Sandbox Design

```python
class ExecutorSandbox:
    """All executor actions go through this sandbox."""

    def __init__(self, permissions: ExecutorPermissions):
        self.permissions = permissions
        self.executed_actions: list[Action] = []

    async def execute(self, action: Action) -> ActionResult:
        # 1. Check action tier
        tier = ACTION_TIERS.get(action.type, ActionTier.FORBIDDEN)
        if tier == ActionTier.FORBIDDEN:
            raise ForbiddenActionError(f"Action {action.type} is forbidden")

        # 2. Check namespace permissions
        if hasattr(action, "namespace"):
            if action.namespace in self.permissions.forbidden_namespaces:
                raise PermissionError(f"Namespace {action.namespace} is off-limits")

        # 3. Check cooldown (prevent rapid repeated actions)
        last_same = next(
            (a for a in reversed(self.executed_actions) if a.type == action.type),
            None
        )
        if last_same and (time.time() - last_same.executed_at) < self.permissions.cooldown_seconds:
            raise CooldownError(f"Must wait {self.permissions.cooldown_seconds}s between same actions")

        # 4. Dry-run first
        dry_run = await self.dry_run(action)
        if not dry_run.success:
            raise DryRunError(dry_run.error)

        # 5. Execute with timeout
        result = await asyncio.wait_for(
            self._execute(action),
            timeout=60
        )

        self.executed_actions.append(action)
        return result
```

### Audit Log (Immutable)

```python
# Use PostgreSQL's built-in auditing. Append-only table.
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    incident_id VARCHAR NOT NULL,
    agent_id VARCHAR NOT NULL,
    action_type VARCHAR NOT NULL,
    action_params JSONB NOT NULL,
    reasoning TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    human_approved BOOLEAN,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
    -- No UPDATE or DELETE allowed on this table
);

-- Revoke delete permission even from the app user
REVOKE DELETE ON audit_log FROM aire_app;
REVOKE UPDATE ON audit_log FROM aire_app;
```

---

## 16. Testing Strategy

### Test Incident Injection

```python
# tests/inject_incidents.py
class IncidentInjector:
    """Simulate real production failures for testing."""

    async def inject_pod_crash(self, namespace: str, deployment: str):
        """Force a pod to crash with OOMKilled."""
        await kubectl.run(f"""
            kubectl exec -n {namespace}
            $(kubectl get pods -n {namespace} -l app={deployment} -o name | head -1)
            -- sh -c 'cat /dev/urandom | head -c 9999999999 > /dev/null'
        """)

    async def inject_high_error_rate(self, service_url: str, duration: int = 60):
        """Send bad requests to create 5xx errors."""
        async def spam_bad_requests():
            for _ in range(1000):
                await httpx.post(f"{service_url}/trigger-error")
                await asyncio.sleep(0.1)
        await asyncio.wait_for(spam_bad_requests(), timeout=duration)

    async def inject_latency_spike(self, namespace: str, deployment: str):
        """Apply network latency using tc (traffic control)."""
        pod = await kubectl.get_pod(namespace, deployment)
        await kubectl.exec(pod, "tc qdisc add dev eth0 root netem delay 5000ms")
```

### Agent Unit Tests

```python
# Test Investigator in isolation
async def test_investigator_finds_deploy_correlation():
    # Mock tools to return controlled data
    mock_tools = MockToolRegistry({
        "query_prometheus": {"result": "error_rate=0.34"},
        "get_deployments": {"deploys": [{"version": "v1.4.2", "time": "14:27:32"}]},
        "search_logs": {"logs": ["14:29:15 ERROR Connection pool exhausted"]}
    })

    agent = InvestigatorAgent(tools=mock_tools, llm=test_llm)
    investigation = await agent.investigate(sample_incident)

    assert "v1.4.2" in investigation.causal_chain
    assert len(investigation.timeline) >= 3
    assert investigation.timeline[0].time < investigation.timeline[-1].time
```

---

## 17. Production Deployment

When you're ready to deploy for real:

### Infrastructure
```
AWS / GCP / Azure
  └── Managed Kubernetes (EKS / GKE / AKS)
       ├── AIRE Namespace
       │    ├── aire-api (FastAPI, 3 replicas)
       │    ├── aire-worker (agent workers, 2 replicas)
       │    └── aire-frontend (Next.js, 2 replicas)
       ├── Observability Namespace
       │    ├── prometheus
       │    ├── loki
       │    └── grafana
       └── Data Namespace
            ├── postgresql (RDS in prod)
            └── redis (ElastiCache in prod)
```

### Multi-Tenant Architecture (for selling to companies)

```python
class TenantConfig(BaseModel):
    tenant_id: str
    kubernetes_contexts: list[str]
    prometheus_urls: list[str]
    loki_url: str
    slack_webhook: str
    jira_project: str
    executor_permissions: ExecutorPermissions
    llm_budget_monthly_usd: float
```

---

## 18. What You'll Learn

After building AIRE, you will genuinely understand:

### AI Engineering
- Multi-agent orchestration (not just chatbots)
- ReAct agent loops (Reason → Act → Observe → Repeat)
- RAG systems for domain-specific retrieval
- Confidence scoring and uncertainty quantification
- Human-in-the-loop design
- Evaluation of agent outputs

### Platform / Systems Engineering
- Kubernetes internals (pods, deployments, events, RBAC)
- Observability (metrics, logs, traces — not just theory)
- Event-driven architecture with Redis Streams
- Distributed system failure modes
- Linux process management and resource limits

### Backend Engineering
- Async Python (asyncio, FastAPI)
- State machines (LangGraph)
- Database design for AI systems (vector search, audit logs)
- WebSocket real-time systems
- gRPC for internal service communication

### Security
- Least-privilege agent design
- Immutable audit trails
- Sandboxing autonomous actions
- Secret rotation automation
- Anomaly detection vs. intrusion detection

---

## 19. Career & Business Path

### This project is a portfolio that speaks for itself

When you interview and show a live demo of:
- A Kubernetes pod crashing
- Your system detecting it in seconds
- Agents reasoning through the cause in real-time
- A rollback executing automatically
- A postmortem appearing in Slack

**That is a hire-on-the-spot moment.** No coding quiz needed.

### Business Models

| Model | How it works | Revenue potential |
|-------|-------------|-------------------|
| **SaaS** | Connect to customer's K8s + Prometheus. $500–5000/month | High |
| **Enterprise on-prem** | Deploy inside their VPC. $50k–200k/year | Very High |
| **Consulting** | Build custom AIRE for a company. $150–300/hr | Medium |
| **Open core** | Free observer/investigator, paid executor + report | Community + SaaS |

### Roles this prepares you for

- **Senior AI Engineer** ($180k–250k) — Agent systems, LLM integration
- **Staff SRE** ($200k–280k) — Observability, incident response, toil reduction
- **Platform Engineer** ($160k–220k) — Internal developer platforms
- **AI Product Engineer** ($170k–240k) — Shipping real AI products

---

## 20. Resources & References

### Must-Read Before Starting

| Resource | What You Learn |
|----------|----------------|
| [Google SRE Book](https://sre.google/sre-book/table-of-contents/) | SRE fundamentals, incident management |
| [Prometheus Docs](https://prometheus.io/docs/introduction/overview/) | Metrics, PromQL |
| [LangGraph Docs](https://langchain-ai.github.io/langgraph/) | Agent state machines |
| [Kubernetes Docs](https://kubernetes.io/docs/home/) | K8s fundamentals |
| Anthropic's agent papers | ReAct, tool use, multi-agent patterns |

### Key Papers

- **ReAct: Synergizing Reasoning and Acting in Language Models** (Yao et al., 2022) — The foundation of your Investigator Agent
- **Toolformer** (Schick et al., 2023) — How LLMs learn to use tools
- **HuggingGPT / JARVIS** (Shen et al., 2023) — Multi-agent task decomposition

### Recommended Learning Order

1. **Week 0 (before coding)**: Read Google SRE Book chapters 1, 2, 12, 14. Understand what an SRE actually does all day.
2. **Week 0**: Build a small K8s app by hand. Deploy it. Break it. Fix it.
3. **Week 0**: Write a simple ReAct agent from scratch (no framework). Understand the loop.
4. **Then**: Start Phase 1.

---

## Quick Start Checklist

```
□ Docker Desktop installed and running
□ k3s installed (curl -sfL https://get.k3s.io | sh -)
□ Python 3.11+ with Poetry
□ Node.js 20+
□ OpenAI or Anthropic API key
□ Git repo created
□ docker-compose up -d (Prometheus, Loki, Grafana, Postgres, Redis)
□ Sample app deployed to k3s
□ Grafana dashboard showing metrics
□ First incident injected manually
□ Observer Agent detecting it (even if just printing to console)
```

---

*Built with: curiosity + persistence. Broken with: bad deploys. Fixed with: AIRE.*

> "The best incident response is the one that happens while you're asleep."
