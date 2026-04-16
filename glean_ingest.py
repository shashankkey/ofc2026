"""
Glean Insights -> Elasticsearch ingestion script.
Fetches overview, assistant, and agents insights and bulk-indexes into ES.
Run as a cron job (e.g. twice daily).

Uses deterministic _id per document so repeated runs upsert instead of duplicating.
"""

import hashlib
import json
import logging
import os
import sys
from datetime import date, datetime, timezone

import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

load_dotenv()

GLEAN_INSTANCE_URL = os.environ["GLEAN_INSTANCE_URL"]
GLEAN_API_TOKEN = os.environ["GLEAN_API_TOKEN"]
ES_HOST = os.environ["ES_HOST"]
ES_USERNAME = os.environ["ES_USERNAME"]
ES_PASSWORD = os.environ["ES_PASSWORD"]
DAYS_FROM_NOW_START = int(os.getenv("DAYS_FROM_NOW_START", "30"))
DAYS_FROM_NOW_END = int(os.getenv("DAYS_FROM_NOW_END", "0"))
INDEX_OVERVIEW = os.getenv("INDEX_OVERVIEW", "glean-insights-overview")
INDEX_ASSISTANT = os.getenv("INDEX_ASSISTANT", "glean-insights-assistant")
INDEX_AGENTS = os.getenv("INDEX_AGENTS", "glean-insights-agents")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Glean API
# ---------------------------------------------------------------------------

def fetch_insights() -> dict:
    url = f"{GLEAN_INSTANCE_URL.rstrip('/')}/rest/api/v1/insights"
    headers = {
        "Authorization": f"Bearer {GLEAN_API_TOKEN}",
        "Content-Type": "application/json",
    }
    day_range = {
        "start": {"daysFromNow": DAYS_FROM_NOW_START},
        "end":   {"daysFromNow": DAYS_FROM_NOW_END},
    }
    body = {
        "overviewRequest":   {"dayRange": day_range},
        "assistantRequest":  {"dayRange": day_range},
        "agentsRequest":     {"dayRange": day_range, "agentIds": []},
        "disablePerUserInsights": True,
    }
    log.info("Fetching Glean insights (last %d days)...", DAYS_FROM_NOW_START)
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _epoch_to_iso(epoch_seconds: int | None) -> str | None:
    """Convert epoch seconds to ISO-8601 UTC string."""
    if epoch_seconds is None:
        return None
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _extract_period(period: dict | None) -> dict:
    """
    Extract start/end epoch seconds from a Period object.
    Period schema:
      { start: { epochSeconds: int, daysFromNow: int },
        end:   { epochSeconds: int, daysFromNow: int } }
    """
    if not period:
        return {"period_start_epoch": None, "period_end_epoch": None,
                "period_start": None, "period_end": None}
    start = (period.get("start") or {}).get("epochSeconds")
    end = (period.get("end") or {}).get("epochSeconds")
    return {
        "period_start_epoch": start,
        "period_end_epoch": end,
        "period_start": _epoch_to_iso(start),
        "period_end": _epoch_to_iso(end),
    }


def _make_id(*parts) -> str:
    """Deterministic doc _id from arbitrary parts."""
    raw = "_".join(str(p) for p in parts if p is not None)
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def _base_meta(ingested_at: str) -> dict:
    return {
        "ingested_at": ingested_at,
        "period_days": DAYS_FROM_NOW_START,
    }


# ---------------------------------------------------------------------------
# Timeseries parser (corrected schema)
# ---------------------------------------------------------------------------

def _timeseries_to_docs(
    labeled_count_info: dict | None,
    metric_name: str,
    granularity: str,
    base: dict,
    doc_type: str,
) -> list[dict]:
    """
    LabeledCountInfo actual schema:
      {
        "label": string,           -- grouping label (category, NOT a date)
        "countInfo": CountInfo[] [
          {
            "count": integer,
            "period": Period {
              "start": TimePoint { "epochSeconds": int, "daysFromNow": int },
              "end":   TimePoint { "epochSeconds": int, "daysFromNow": int }
            },
            "org": string
          }
        ]
      }

    Produces one ES doc per countInfo entry per label.
    Uses period.start.epochSeconds as @timestamp for Kibana.
    """
    if not labeled_count_info:
        return []

    label = labeled_count_info.get("label", "")
    count_infos = labeled_count_info.get("countInfo") or []
    docs = []

    for ci in count_infos:
        count = ci.get("count")
        if count is None:
            continue

        period_data = _extract_period(ci.get("period"))
        org = ci.get("org")

        doc_id = _make_id(
            doc_type, metric_name, label, org,
            period_data["period_start_epoch"],
            period_data["period_end_epoch"],
        )

        doc = {
            **base,
            "doc_type": doc_type,
            "metric": metric_name,
            "granularity": granularity,
            "label": label,
            "count": count,
            "org": org,
            **period_data,
            "@timestamp": period_data["period_start"] or base["ingested_at"],
        }
        docs.append({"_id": doc_id, "_doc": doc})

    return docs


# ---------------------------------------------------------------------------
# Document builders
# ---------------------------------------------------------------------------

def build_overview_docs(data: dict, ingested_at: str) -> list[dict]:
    r = data.get("overviewResponse", {})
    if not r:
        log.warning("overviewResponse missing in API response")
        return []

    docs = []
    base = _base_meta(ingested_at)
    today = date.today().isoformat()

    # --- Scalar summary document ---
    summary_id = _make_id("overview_summary", today)
    summary = {
        **base,
        "doc_type": "overview_summary",
        "monthly_active_users": r.get("monthlyActiveUsers"),
        "weekly_active_users": r.get("weeklyActiveUsers"),
        "employee_count": r.get("employeeCount"),
        "total_signups": r.get("totalSignups"),
        "search_session_satisfaction": r.get("searchSessionSatisfaction"),
        "last_updated_ts": r.get("lastUpdatedTs"),
        "departments": r.get("departments", []),
        "@timestamp": ingested_at,
    }

    for key, area in [
        ("searchActiveUsers", "search"),
        ("assistantActiveUsers", "assistant"),
        ("agentsActiveUsers", "agents"),
    ]:
        obj = r.get(key) or {}
        summary[f"{area}_mau"] = obj.get("monthlyActiveUsers")
        summary[f"{area}_wau"] = obj.get("weeklyActiveUsers")
        summary[f"{area}_dau"] = obj.get("dailyActiveUsers")

    for key, prefix in [
        ("searchSummary", "search"),
        ("chatSummary", "chat"),
        ("extensionSummary", "extension"),
        ("ugcSummary", "ugc"),
    ]:
        obj = r.get(key) or {}
        for k, v in obj.items():
            summary[f"{prefix}_{k}"] = v

    # Datasource counts (dynamic keys)
    for key, prefix in [("searchDatasourceCounts", "search_ds"), ("chatDatasourceCounts", "chat_ds")]:
        obj = r.get(key) or {}
        for ds_name, ds_count in obj.items():
            summary[f"{prefix}_{ds_name}"] = ds_count

    docs.append({"_id": summary_id, "_doc": summary})

    # --- Timeseries ---
    timeseries_fields = [
        ("monthlyActiveUserTimeseries",          "mau_all",                "monthly"),
        ("weeklyActiveUserTimeseries",           "wau_all",                "weekly"),
        ("dailyActiveUserTimeseries",            "dau_all",                "daily"),
        ("searchMonthlyActiveUserTimeseries",    "mau_search",             "monthly"),
        ("searchWeeklyActiveUserTimeseries",     "wau_search",             "weekly"),
        ("searchDailyActiveUserTimeseries",      "dau_search",             "daily"),
        ("assistantMonthlyActiveUserTimeseries", "mau_assistant",          "monthly"),
        ("assistantWeeklyActiveUserTimeseries",  "wau_assistant",          "weekly"),
        ("assistantDailyActiveUserTimeseries",   "dau_assistant",          "daily"),
        ("agentsMonthlyActiveUserTimeseries",    "mau_agents",             "monthly"),
        ("agentsWeeklyActiveUserTimeseries",     "wau_agents",             "weekly"),
        ("agentsDailyActiveUserTimeseries",      "dau_agents",             "daily"),
        ("searchesTimeseries",                   "searches",               "daily"),
        ("assistantInteractionsTimeseries",      "assistant_interactions", "daily"),
        ("agentRunsTimeseries",                  "agent_runs",             "daily"),
    ]
    for field, metric_name, granularity in timeseries_fields:
        docs.extend(_timeseries_to_docs(
            r.get(field), metric_name, granularity, base, "overview_timeseries"
        ))

    return docs


def build_assistant_docs(data: dict, ingested_at: str) -> list[dict]:
    r = data.get("assistantResponse", {})
    if not r:
        log.warning("assistantResponse missing in API response")
        return []

    docs = []
    base = _base_meta(ingested_at)
    today = date.today().isoformat()

    summary_id = _make_id("assistant_summary", today)
    summary = {
        **base,
        "doc_type": "assistant_summary",
        "monthly_active_users": r.get("monthlyActiveUsers"),
        "weekly_active_users": r.get("weeklyActiveUsers"),
        "total_signups": r.get("totalSignups"),
        "last_updated_ts": r.get("lastUpdatedTs"),
        "@timestamp": ingested_at,
    }
    docs.append({"_id": summary_id, "_doc": summary})

    timeseries_fields = [
        ("monthlyActiveUserTimeseries",    "mau",                   "monthly"),
        ("weeklyActiveUserTimeseries",     "wau",                   "weekly"),
        ("dailyActiveUserTimeseries",      "dau",                   "daily"),
        ("chatMessagesTimeseries",         "chat_messages",         "daily"),
        ("summarizationsTimeseries",       "summarizations",        "daily"),
        ("aiAnswersTimeseries",            "ai_answers",            "daily"),
        ("gleanbotInteractionsTimeseries", "gleanbot_interactions", "daily"),
        ("upvotesTimeseries",              "upvotes",               "daily"),
        ("downvotesTimeseries",            "downvotes",             "daily"),
    ]
    for field, metric_name, granularity in timeseries_fields:
        docs.extend(_timeseries_to_docs(
            r.get(field), metric_name, granularity, base, "assistant_timeseries"
        ))

    return docs


def build_agents_docs(data: dict, ingested_at: str) -> list[dict]:
    r = data.get("agentsResponse", {})
    if not r:
        log.warning("agentsResponse missing in API response")
        return []

    docs = []
    base = _base_meta(ingested_at)
    today = date.today().isoformat()

    # --- Summary ---
    summary_id = _make_id("agents_summary", today)
    summary = {
        **base,
        "doc_type": "agents_summary",
        "monthly_active_users": r.get("monthlyActiveUsers"),
        "weekly_active_users": r.get("weeklyActiveUsers"),
        "shared_agents_count": r.get("sharedAgentsCount"),
        "@timestamp": ingested_at,
    }
    docs.append({"_id": summary_id, "_doc": summary})

    # --- Top agents ---
    for agent in r.get("topAgentsInsights") or []:
        agent_id = _make_id("agent_top", today, agent.get("agentId", agent.get("name", "")))
        docs.append({
            "_id": agent_id,
            "_doc": {**base, "doc_type": "agent_top", "@timestamp": ingested_at, **agent},
        })

    # --- Usage by department ---
    for dept in r.get("agentsUsageByDepartmentInsights") or []:
        dept_id = _make_id("agent_dept_usage", today, dept.get("department", ""))
        docs.append({
            "_id": dept_id,
            "_doc": {**base, "doc_type": "agent_dept_usage", "@timestamp": ingested_at, **dept},
        })

    # --- Time saved ---
    for ts in r.get("agentsTimeSavedInsights") or []:
        ts_id = _make_id("agent_time_saved", today, ts.get("agentId", ts.get("name", "")))
        docs.append({
            "_id": ts_id,
            "_doc": {**base, "doc_type": "agent_time_saved", "@timestamp": ingested_at, **ts},
        })

    # --- Timeseries ---
    timeseries_fields = [
        ("monthlyActiveUserTimeseries",  "mau",          "monthly"),
        ("weeklyActiveUserTimeseries",   "wau",          "weekly"),
        ("dailyActiveUserTimeseries",    "dau",          "daily"),
        ("dailyAgentRunsTimeseries",     "agent_runs",   "daily"),
        ("successfulRunsTimeseries",     "runs_success", "daily"),
        ("failedRunsTimeseries",         "runs_failed",  "daily"),
        ("pausedRunsTimeseries",         "runs_paused",  "daily"),
        ("upvotesTimeseries",            "upvotes",      "daily"),
        ("downvotesTimeseries",          "downvotes",    "daily"),
    ]
    for field, metric_name, granularity in timeseries_fields:
        docs.extend(_timeseries_to_docs(
            r.get(field), metric_name, granularity, base, "agents_timeseries"
        ))

    return docs


# ---------------------------------------------------------------------------
# Elasticsearch
# ---------------------------------------------------------------------------

def get_es_client() -> Elasticsearch:
    return Elasticsearch(
        ES_HOST,
        basic_auth=(ES_USERNAME, ES_PASSWORD),
        verify_certs=True,
    )


def ensure_index(es: Elasticsearch, index: str) -> None:
    if es.indices.exists(index=index):
        return
    mapping = {
        "mappings": {
            "properties": {
                "ingested_at":        {"type": "date"},
                "@timestamp":         {"type": "date"},
                "last_updated_ts":    {"type": "date", "format": "epoch_second"},
                "period_start":       {"type": "date"},
                "period_end":         {"type": "date"},
                "period_start_epoch": {"type": "long"},
                "period_end_epoch":   {"type": "long"},
                "count":              {"type": "long"},
                "metric":             {"type": "keyword"},
                "doc_type":           {"type": "keyword"},
                "granularity":        {"type": "keyword"},
                "label":              {"type": "keyword"},
                "org":                {"type": "keyword"},
            }
        }
    }
    es.indices.create(index=index, body=mapping)
    log.info("Created index: %s", index)


def index_docs(es: Elasticsearch, index: str, docs: list[dict]) -> None:
    if not docs:
        log.info("No documents to index for %s", index)
        return

    actions = [
        {"_index": index, "_id": d["_id"], "_source": d["_doc"]}
        for d in docs
    ]
    success, errors = bulk(es, actions, raise_on_error=False)
    log.info("Indexed %d docs into %s", success, index)
    if errors:
        log.error("Bulk errors for %s: %s", index, json.dumps(errors[:5]))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ingested_at = datetime.now(timezone.utc).isoformat()
    log.info("Starting Glean insights ingestion at %s", ingested_at)

    try:
        data = fetch_insights()
    except requests.HTTPError as e:
        log.error("Glean API error: %s — %s", e.response.status_code, e.response.text)
        sys.exit(1)
    except requests.RequestException as e:
        log.error("Glean API request failed: %s", e)
        sys.exit(1)

    overview_docs  = build_overview_docs(data, ingested_at)
    assistant_docs = build_assistant_docs(data, ingested_at)
    agents_docs    = build_agents_docs(data, ingested_at)

    log.info(
        "Built %d overview / %d assistant / %d agents documents",
        len(overview_docs), len(assistant_docs), len(agents_docs),
    )

    es = get_es_client()
    for index, docs in [
        (INDEX_OVERVIEW,   overview_docs),
        (INDEX_ASSISTANT,  assistant_docs),
        (INDEX_AGENTS,     agents_docs),
    ]:
        ensure_index(es, index)
        index_docs(es, index, docs)

    log.info("Ingestion complete.")


if __name__ == "__main__":
    main()
