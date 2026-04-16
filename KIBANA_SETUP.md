# Kibana Setup Guide — Glean Insights Dashboards

Run these steps after first successful `python glean_ingest.py`.

---

## Step 1 — Create Data Views

Go to **Stack Management → Data Views → Create data view**

| Name | Index pattern | Time field |
|---|---|---|
| `glean-overview` | `glean-insights-overview` | `@timestamp` |
| `glean-assistant` | `glean-insights-assistant` | `@timestamp` |
| `glean-agents` | `glean-insights-agents` | `@timestamp` |

---

## Step 2 — Dashboard: Glean — Platform Overview

**Data view:** `glean-overview` | **Default time range:** Last 30 days

This dashboard gives a cross-product view of Glean adoption — how many people are active, across search, assistant, and agents.

---

### Row 1 — KPI Metrics

> Single-value metric panels. Use **Lens → Metric** visualization. Aggregation = **Max**. Add KQL filter `doc_type: "overview_summary"` on each.

| # | Title | Field | Description |
|---|---|---|---|
| 1 | Monthly Active Users | `monthly_active_users` | Total unique users who used any Glean product in the last 30 days across all departments |
| 2 | Weekly Active Users | `weekly_active_users` | Total unique users active in the last 7 days — indicates recent engagement momentum |
| 3 | Employee Count | `employee_count` | Total headcount from the org chart — use as denominator to calculate adoption % |
| 4 | Total Signups | `total_signups` | Total employees who have signed up for Glean — shows onboarding reach vs employee count |
| 5 | Search Session Satisfaction | `search_session_satisfaction` | Float 0–1 representing search session satisfaction rate over the period — key quality signal |
| 6 | Total Searches | `search_numSearches` | Total number of searches performed in the period |

---

### Row 2 — Daily Active Users by Product (Line Charts)

> Use **Lens → Line chart**. X-axis = `@timestamp` (date histogram, interval: `1d`), Y-axis = `count` (Sum). Add KQL filter per panel. Data view: `glean-overview`, `doc_type: "overview_timeseries"`.

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 7 | All Users — DAU | `doc_type: "overview_timeseries" AND metric: "dau_all"` | Daily count of unique active users across all Glean products combined — shows overall platform engagement trend |
| 8 | Search — DAU | `doc_type: "overview_timeseries" AND metric: "dau_search"` | Daily unique users who performed at least one search — tracks core search product adoption over time |

---

### Row 3 — Assistant & Agents DAU (Line Charts)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 9 | Assistant — DAU | `doc_type: "overview_timeseries" AND metric: "dau_assistant"` | Daily unique users of Glean Assistant (chat/AI) — tracks AI feature adoption separate from search |
| 10 | Agents — DAU | `doc_type: "overview_timeseries" AND metric: "dau_agents"` | Daily unique users who ran at least one Glean Agent — tracks agentic workflow adoption |

---

### Row 4 — Activity Volume (Line Charts)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 11 | Daily Search Volume | `doc_type: "overview_timeseries" AND metric: "searches"` | Total number of searches per day (not unique users) — spikes indicate high-demand periods or new team onboarding |
| 12 | Daily Assistant Interactions | `doc_type: "overview_timeseries" AND metric: "assistant_interactions"` | Total assistant interactions per day including chat messages, AI answers, and summarizations — shows AI usage intensity |

---

### Row 5 — Agent Runs (Line Chart)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 13 | Daily Agent Runs (Overview) | `doc_type: "overview_timeseries" AND metric: "agent_runs"` | Total agent executions per day across all agents and users — high-level view of automation activity |

---

### Row 6 — MAU/WAU Trends (optional, Line Charts)

> These show rolling active user counts over time — useful for detecting growth or churn trends.

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 14 | All Users MAU Trend | `doc_type: "overview_timeseries" AND metric: "mau_all"` | Rolling monthly active users over time — the primary adoption health metric |
| 15 | All Users WAU Trend | `doc_type: "overview_timeseries" AND metric: "wau_all"` | Rolling weekly active users — more sensitive to short-term changes than MAU |
| 16 | Search MAU | `doc_type: "overview_timeseries" AND metric: "mau_search"` | Monthly active search users — tracks search product stickiness |
| 17 | Assistant MAU | `doc_type: "overview_timeseries" AND metric: "mau_assistant"` | Monthly active assistant users — tracks AI feature stickiness |
| 18 | Agents MAU | `doc_type: "overview_timeseries" AND metric: "mau_agents"` | Monthly active agents users — tracks agentic workflow adoption growth |

---

## Step 3 — Dashboard: Glean — Assistant Analytics

**Data view:** `glean-assistant` | **Default time range:** Last 30 days

This dashboard focuses on Glean's AI assistant — chat, summarizations, AI answers, Gleanbot, and user satisfaction signals.

---

### Row 1 — KPI Metrics

> **Lens → Metric**, aggregation = **Max**, KQL filter = `doc_type: "assistant_summary"` on each.

| # | Title | Field | Description |
|---|---|---|---|
| 1 | MAU (Assistant) | `monthly_active_users` | Monthly active users of Glean Assistant — baseline adoption metric for the AI product |
| 2 | WAU (Assistant) | `weekly_active_users` | Weekly active users — tracks week-over-week engagement with the assistant |
| 3 | Total Signups | `total_signups` | Total employees signed up — use with MAU to calculate assistant activation rate (MAU / signups) |

---

### Row 2 — Daily Active Users & Chat Volume (Line Charts)

> **Lens → Line chart**. X-axis = `@timestamp` (1d interval), Y-axis = `count` (Sum). Filter: `doc_type: "assistant_timeseries"`.

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 4 | Assistant — DAU | `doc_type: "assistant_timeseries" AND metric: "dau"` | Daily unique users of the assistant — distinguishes between users and total interaction volume |
| 5 | Chat Messages | `doc_type: "assistant_timeseries" AND metric: "chat_messages"` | Total chat messages sent per day — measures raw usage intensity; high values indicate deep assistant engagement |

---

### Row 3 — AI Feature Usage (Line Charts)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 6 | AI Answers | `doc_type: "assistant_timeseries" AND metric: "ai_answers"` | Daily count of AI-generated answers served — tracks how often users get direct AI responses vs. standard search results |
| 7 | Summarizations | `doc_type: "assistant_timeseries" AND metric: "summarizations"` | Daily document summarizations triggered — indicates how often users use Glean to digest long content |

---

### Row 4 — Gleanbot & Satisfaction (Line Charts)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 8 | Gleanbot Interactions | `doc_type: "assistant_timeseries" AND metric: "gleanbot_interactions"` | Daily interactions with Gleanbot (Slack/Teams bot) — tracks assistant usage outside the main Glean UI |
| 9 | Upvotes | `doc_type: "assistant_timeseries" AND metric: "upvotes"` | Daily positive feedback signals from users — indicates responses were helpful; use with downvotes for satisfaction ratio |
| 10 | Downvotes | `doc_type: "assistant_timeseries" AND metric: "downvotes"` | Daily negative feedback signals — spikes indicate quality issues; compare against upvotes to track satisfaction trend |

> **Tip:** To compare upvotes vs downvotes on a single chart, create a **Lens → Line chart** with two layers — one filtered `metric: "upvotes"`, one filtered `metric: "downvotes"`, both with `count` Sum on Y-axis.

---

### Row 5 — MAU/WAU Trend (Line Charts, optional)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 11 | Assistant MAU Trend | `doc_type: "assistant_timeseries" AND metric: "mau"` | Rolling 30-day active assistant users — key signal for long-term AI adoption growth |
| 12 | Assistant WAU Trend | `doc_type: "assistant_timeseries" AND metric: "wau"` | Rolling 7-day active assistant users — more responsive to recent campaigns or feature releases |

---

## Step 4 — Dashboard: Glean — Agents Analytics

**Data view:** `glean-agents` | **Default time range:** Last 30 days

This dashboard covers Glean Agents — who is using them, which agents are most popular, run health, and estimated time savings.

---

### Row 1 — KPI Metrics

> **Lens → Metric**, aggregation = **Max**, KQL filter = `doc_type: "agents_summary"` on each.

| # | Title | Field | Description |
|---|---|---|---|
| 1 | MAU (Agents) | `monthly_active_users` | Monthly active users who ran at least one agent — primary adoption metric for the agents product |
| 2 | WAU (Agents) | `weekly_active_users` | Weekly active agent users — tracks recency of engagement |
| 3 | Shared Agents | `shared_agents_count` | Total number of agents shared across the org — indicates how many reusable automations have been created |

---

### Row 2 — Run Volume & Health (Line Charts)

> **Lens → Line chart**. X-axis = `@timestamp` (1d interval), Y-axis = `count` (Sum). Filter: `doc_type: "agents_timeseries"`.

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 4 | Daily Agent Runs | `doc_type: "agents_timeseries" AND metric: "agent_runs"` | Total agent executions per day across all agents — primary volume metric for the agents platform |
| 5 | Successful Runs | `doc_type: "agents_timeseries" AND metric: "runs_success"` | Daily count of agent runs that completed successfully — high values vs total runs = healthy platform |

---

### Row 3 — Run Failures (Line Charts)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 6 | Failed Runs | `doc_type: "agents_timeseries" AND metric: "runs_failed"` | Daily count of agent runs that failed — spikes here warrant investigation into specific agent errors |
| 7 | Paused Runs | `doc_type: "agents_timeseries" AND metric: "runs_paused"` | Daily count of runs paused mid-execution — may indicate agents requiring human intervention or hitting timeouts |

---

### Row 4 — Agent Satisfaction (Line Charts)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 8 | Agent Upvotes | `doc_type: "agents_timeseries" AND metric: "upvotes"` | Daily positive ratings on agent runs — users rating a run as helpful; high values indicate agents delivering real value |
| 9 | Agent Downvotes | `doc_type: "agents_timeseries" AND metric: "downvotes"` | Daily negative ratings — an agent consistently receiving downvotes needs review or retraining |

---

### Row 5 — Top Agents (Horizontal Bar Charts)

> **Lens → Bar horizontal**. Terms bucket on X-axis (top 10 desc), Max aggregation on Y-axis.

| # | Title | X-axis (Terms) | Y-axis (Max) | KQL Filter | Description |
|---|---|---|---|---|---|
| 10 | Top Agents by Run Count | `agentName` | `runCount` | `doc_type: "agent_top"` | Ranks agents by total executions — identifies the most-used automations in the org |
| 11 | Top Agents by User Count | `agentName` | `userCount` | `doc_type: "agent_top"` | Ranks agents by number of unique users — distinguishes widely-adopted agents from ones used heavily by few people |

---

### Row 6 — Department Adoption (Horizontal Bar Charts)

| # | Title | X-axis (Terms) | Y-axis (Max) | KQL Filter | Description |
|---|---|---|---|---|---|
| 12 | Agent Usage by Department | `department` | `runCount` | `doc_type: "agent_dept_usage"` | Total agent runs per department — identifies which teams are most active with agents |
| 13 | Agent Adoption Rate by Department | `department` | `agentAdoptionRate` | `doc_type: "agent_dept_usage"` | Fraction of department members using agents — highlights departments with high vs low agent adoption regardless of size |

---

### Row 7 — Time Saved (Horizontal Bar Chart)

| # | Title | X-axis (Terms) | Y-axis (Max) | KQL Filter | Description |
|---|---|---|---|---|---|
| 14 | Estimated Minutes Saved per Run | `agentName` | `minsPerRun` | `doc_type: "agent_time_saved"` | Estimated minutes saved per agent execution — useful for ROI reporting; agents with high minsPerRun deliver the most time value |

---

### Row 8 — Data Tables

> Use **Lens → Table** or **Discover** saved search.

| # | Title | Columns | KQL Filter | Description |
|---|---|---|---|---|
| 15 | Top Agents Detail | `agentName`, `userCount`, `runCount`, `upvoteCount`, `downvoteCount` | `doc_type: "agent_top"` | Full leaderboard of agents with satisfaction signals — lets you compare run volume against upvote/downvote ratio to find high-value vs problematic agents |
| 16 | Department Breakdown | `department`, `agentAdoptionRate`, `userCount`, `runCount` | `doc_type: "agent_dept_usage"` | Per-department agent usage detail — useful for targeted enablement campaigns in low-adoption departments |
| 17 | Time Savings Summary | `agentName`, `runCount`, `minsPerRun` | `doc_type: "agent_time_saved"` | Agent-level time savings data — multiply `runCount` × `minsPerRun` in a scripted field to get total minutes saved per agent |

---

### Row 9 — MAU/WAU Trend (Line Charts, optional)

| # | Title | KQL Filter | Description |
|---|---|---|---|
| 18 | Agents MAU Trend | `doc_type: "agents_timeseries" AND metric: "mau"` | Rolling monthly active agent users — shows long-term agents adoption trajectory |
| 19 | Agents WAU Trend | `doc_type: "agents_timeseries" AND metric: "wau"` | Rolling weekly active agent users — more responsive to recent releases or new agent deployments |

---

## Field Reference

### doc_type values

| doc_type | Index | Description |
|---|---|---|
| `overview_summary` | overview | One doc per day — platform-wide scalar metrics |
| `overview_timeseries` | overview | One doc per metric per period per label/org |
| `assistant_summary` | assistant | One doc per day — assistant scalar metrics |
| `assistant_timeseries` | assistant | One doc per metric per period per label/org |
| `agents_summary` | agents | One doc per day — agents scalar metrics |
| `agent_top` | agents | One doc per agent per day — top agent stats |
| `agent_dept_usage` | agents | One doc per department per day — dept usage |
| `agent_time_saved` | agents | One doc per agent per day — time savings |
| `agents_timeseries` | agents | One doc per metric per period per label/org |

### metric values (timeseries docs)

| metric | Index | Granularity | Description |
|---|---|---|---|
| `dau_all` | overview | daily | All-product daily active users |
| `wau_all` | overview | weekly | All-product weekly active users |
| `mau_all` | overview | monthly | All-product monthly active users |
| `dau_search` | overview | daily | Search daily active users |
| `wau_search` | overview | weekly | Search weekly active users |
| `mau_search` | overview | monthly | Search monthly active users |
| `dau_assistant` | overview | daily | Assistant daily active users |
| `wau_assistant` | overview | weekly | Assistant weekly active users |
| `mau_assistant` | overview | monthly | Assistant monthly active users |
| `dau_agents` | overview | daily | Agents daily active users |
| `wau_agents` | overview | weekly | Agents weekly active users |
| `mau_agents` | overview | monthly | Agents monthly active users |
| `searches` | overview | daily | Total search count |
| `assistant_interactions` | overview | daily | Total assistant interactions |
| `agent_runs` | overview | daily | Total agent runs (cross-product view) |
| `dau` | assistant | daily | Assistant daily active users |
| `wau` | assistant | weekly | Assistant weekly active users |
| `mau` | assistant | monthly | Assistant monthly active users |
| `chat_messages` | assistant | daily | Chat messages sent |
| `summarizations` | assistant | daily | Summarizations triggered |
| `ai_answers` | assistant | daily | AI answers served |
| `gleanbot_interactions` | assistant | daily | Gleanbot interactions |
| `upvotes` | assistant | daily | Positive feedback on assistant |
| `downvotes` | assistant | daily | Negative feedback on assistant |
| `dau` | agents | daily | Agents daily active users |
| `wau` | agents | weekly | Agents weekly active users |
| `mau` | agents | monthly | Agents monthly active users |
| `agent_runs` | agents | daily | Total agent runs |
| `runs_success` | agents | daily | Successful agent runs |
| `runs_failed` | agents | daily | Failed agent runs |
| `runs_paused` | agents | daily | Paused agent runs |
| `upvotes` | agents | daily | Positive feedback on agents |
| `downvotes` | agents | daily | Negative feedback on agents |
