# Kibana Setup Guide — Glean Insights Dashboards

Run these steps after first successful `python glean_ingest.py`.

---

## 1. Create Data Views

Go to **Stack Management > Data Views > Create data view** and create 3:

| Name | Index pattern | Time field |
|---|---|---|
| `glean-overview` | `glean-insights-overview` | `@timestamp` |
| `glean-assistant` | `glean-insights-assistant` | `@timestamp` |
| `glean-agents` | `glean-insights-agents` | `@timestamp` |

---

## 2. Dashboard: Glean — Platform Overview

Data view: `glean-overview` | Time range: Last 30 days

### Metric Panels (top row)

| Title | Visualization | Field | Filter |
|---|---|---|---|
| Monthly Active Users | Metric (max) | `monthly_active_users` | `doc_type: "overview_summary"` |
| Weekly Active Users | Metric (max) | `weekly_active_users` | `doc_type: "overview_summary"` |
| Employee Count | Metric (max) | `employee_count` | `doc_type: "overview_summary"` |
| Total Signups | Metric (max) | `total_signups` | `doc_type: "overview_summary"` |

### Timeseries Panels (line charts)

For each: X-axis = `@timestamp` (date histogram, auto), Y-axis = `count` (sum)

| Title | KQL Filter |
|---|---|
| All Users — DAU | `doc_type: "overview_timeseries" AND metric: "dau_all"` |
| Search — DAU | `doc_type: "overview_timeseries" AND metric: "dau_search"` |
| Assistant — DAU | `doc_type: "overview_timeseries" AND metric: "dau_assistant"` |
| Agents — DAU | `doc_type: "overview_timeseries" AND metric: "dau_agents"` |
| Daily Searches Volume | `doc_type: "overview_timeseries" AND metric: "searches"` |
| Assistant Interactions | `doc_type: "overview_timeseries" AND metric: "assistant_interactions"` |
| Agent Runs | `doc_type: "overview_timeseries" AND metric: "agent_runs"` |

### Optional — MAU/WAU Trend Lines

| Title | KQL Filter |
|---|---|
| All Users — MAU | `doc_type: "overview_timeseries" AND metric: "mau_all"` |
| All Users — WAU | `doc_type: "overview_timeseries" AND metric: "wau_all"` |
| Search — MAU | `doc_type: "overview_timeseries" AND metric: "mau_search"` |
| Search — WAU | `doc_type: "overview_timeseries" AND metric: "wau_search"` |
| Assistant — MAU | `doc_type: "overview_timeseries" AND metric: "mau_assistant"` |
| Assistant — WAU | `doc_type: "overview_timeseries" AND metric: "wau_assistant"` |
| Agents — MAU | `doc_type: "overview_timeseries" AND metric: "mau_agents"` |
| Agents — WAU | `doc_type: "overview_timeseries" AND metric: "wau_agents"` |

---

## 3. Dashboard: Glean — Assistant Analytics

Data view: `glean-assistant` | Time range: Last 30 days

### Metric Panels

| Title | Visualization | Field | Filter |
|---|---|---|---|
| MAU (Assistant) | Metric (max) | `monthly_active_users` | `doc_type: "assistant_summary"` |
| WAU (Assistant) | Metric (max) | `weekly_active_users` | `doc_type: "assistant_summary"` |
| Total Signups | Metric (max) | `total_signups` | `doc_type: "assistant_summary"` |

### Timeseries Panels

X-axis = `@timestamp`, Y-axis = `count` (sum)

| Title | KQL Filter |
|---|---|
| Daily Active Users | `doc_type: "assistant_timeseries" AND metric: "dau"` |
| Chat Messages | `doc_type: "assistant_timeseries" AND metric: "chat_messages"` |
| AI Answers | `doc_type: "assistant_timeseries" AND metric: "ai_answers"` |
| Summarizations | `doc_type: "assistant_timeseries" AND metric: "summarizations"` |
| Gleanbot Interactions | `doc_type: "assistant_timeseries" AND metric: "gleanbot_interactions"` |
| Upvotes | `doc_type: "assistant_timeseries" AND metric: "upvotes"` |
| Downvotes | `doc_type: "assistant_timeseries" AND metric: "downvotes"` |

### Optional — MAU/WAU

| Title | KQL Filter |
|---|---|
| MAU Trend | `doc_type: "assistant_timeseries" AND metric: "mau"` |
| WAU Trend | `doc_type: "assistant_timeseries" AND metric: "wau"` |

---

## 4. Dashboard: Glean — Agents Analytics

Data view: `glean-agents` | Time range: Last 30 days

### Metric Panels

| Title | Visualization | Field | Filter |
|---|---|---|---|
| MAU (Agents) | Metric (max) | `monthly_active_users` | `doc_type: "agents_summary"` |
| WAU (Agents) | Metric (max) | `weekly_active_users` | `doc_type: "agents_summary"` |
| Shared Agents Count | Metric (max) | `shared_agents_count` | `doc_type: "agents_summary"` |

### Timeseries Panels

X-axis = `@timestamp`, Y-axis = `count` (sum)

| Title | KQL Filter |
|---|---|
| Daily Agent Runs | `doc_type: "agents_timeseries" AND metric: "agent_runs"` |
| Successful Runs | `doc_type: "agents_timeseries" AND metric: "runs_success"` |
| Failed Runs | `doc_type: "agents_timeseries" AND metric: "runs_failed"` |
| Paused Runs | `doc_type: "agents_timeseries" AND metric: "runs_paused"` |
| Agent Upvotes | `doc_type: "agents_timeseries" AND metric: "upvotes"` |
| Agent Downvotes | `doc_type: "agents_timeseries" AND metric: "downvotes"` |

### Optional — MAU/WAU

| Title | KQL Filter |
|---|---|
| MAU Trend | `doc_type: "agents_timeseries" AND metric: "mau"` |
| WAU Trend | `doc_type: "agents_timeseries" AND metric: "wau"` |
| DAU Trend | `doc_type: "agents_timeseries" AND metric: "dau"` |

### Bar Charts (horizontal bar, top 10)

| Title | X-axis (terms) | Y-axis | KQL Filter |
|---|---|---|---|
| Top Agents by Usage | `agentName` | `runCount` (max) | `doc_type: "agent_top"` |
| Usage by Department | `department` | `runCount` (max) | `doc_type: "agent_dept_usage"` |
| Time Saved by Agent | `agentName` | `minsPerRun` (max) | `doc_type: "agent_time_saved"` |

### Data Tables

| Title | Columns | KQL Filter |
|---|---|---|
| Top Agents Detail | `agentName`, `userCount`, `runCount`, `upvoteCount`, `downvoteCount` | `doc_type: "agent_top"` |
| Department Adoption | `department`, `agentAdoptionRate`, `userCount`, `runCount` | `doc_type: "agent_dept_usage"` |

---

## Field Reference

### Common fields (all indices)

| Field | Type | Description |
|---|---|---|
| `@timestamp` | date | Period start (timeseries) or ingestion time (summaries) |
| `ingested_at` | date | When the data was pulled from Glean |
| `doc_type` | keyword | Document type (for filtering) |
| `period_days` | integer | Rolling window size (default 30) |

### Timeseries fields

| Field | Type | Description |
|---|---|---|
| `metric` | keyword | Metric name (e.g. `dau_all`, `searches`) |
| `granularity` | keyword | `daily`, `weekly`, or `monthly` |
| `label` | keyword | Grouping label from Glean |
| `count` | long | Metric value |
| `org` | keyword | Organization unit (department/company) |
| `period_start` | date | Data point period start |
| `period_end` | date | Data point period end |

### Summary-only fields (overview)

| Field | Type |
|---|---|
| `monthly_active_users` | integer |
| `weekly_active_users` | integer |
| `employee_count` | integer |
| `total_signups` | integer |
| `search_session_satisfaction` | float |
| `search_mau`, `search_wau`, `search_dau` | integer |
| `assistant_mau`, `assistant_wau`, `assistant_dau` | integer |
| `agents_mau`, `agents_wau`, `agents_dau` | integer |

### Agent-specific fields

| Field | Type | Doc type |
|---|---|---|
| `agentId` | keyword | agent_top, agent_time_saved |
| `agentName` | keyword | agent_top, agent_dept_usage, agent_time_saved |
| `userCount` | integer | agent_top, agent_dept_usage |
| `runCount` | integer | agent_top, agent_dept_usage, agent_time_saved |
| `upvoteCount` / `downvoteCount` | integer | agent_top |
| `department` | keyword | agent_dept_usage |
| `agentAdoptionRate` | float | agent_dept_usage |
| `minsPerRun` | integer | agent_time_saved |
