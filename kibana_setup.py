"""
Creates Kibana data views + dashboards for Glean insights indices.
Run once after first successful ingestion.
"""

import json
import logging
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

ES_HOST = os.environ["ES_HOST"]
ES_USERNAME = os.environ["ES_USERNAME"]
ES_PASSWORD = os.environ["ES_PASSWORD"]
INDEX_OVERVIEW = os.getenv("INDEX_OVERVIEW", "glean-insights-overview")
INDEX_ASSISTANT = os.getenv("INDEX_ASSISTANT", "glean-insights-assistant")
INDEX_AGENTS = os.getenv("INDEX_AGENTS", "glean-insights-agents")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

KIBANA_URL = os.getenv("KIBANA_URL", ES_HOST.replace(":9200", ":5601"))
KIBANA_HEADERS = {
    "kbn-xsrf": "true",
    "Content-Type": "application/json",
}
KIBANA_AUTH = (ES_USERNAME, ES_PASSWORD)


def kibana_post(path: str, body: dict) -> dict:
    url = f"{KIBANA_URL.rstrip('/')}{path}"
    resp = requests.post(url, headers=KIBANA_HEADERS, auth=KIBANA_AUTH, json=body, timeout=30)
    if resp.status_code not in (200, 201):
        log.error("Kibana POST %s failed %d: %s", path, resp.status_code, resp.text[:500])
        resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Data views (index patterns)
# ---------------------------------------------------------------------------

DATA_VIEWS = [
    {
        "id": "glean-overview",
        "title": INDEX_OVERVIEW,
        "timeFieldName": "@timestamp",
    },
    {
        "id": "glean-assistant",
        "title": INDEX_ASSISTANT,
        "timeFieldName": "@timestamp",
    },
    {
        "id": "glean-agents",
        "title": INDEX_AGENTS,
        "timeFieldName": "@timestamp",
    },
]


def create_data_views() -> None:
    for dv in DATA_VIEWS:
        try:
            result = kibana_post(
                "/api/data_views/data_view",
                {"data_view": dv},
            )
            log.info("Created data view: %s", result.get("data_view", {}).get("title"))
        except requests.HTTPError:
            log.warning("Data view %s may already exist, skipping.", dv["title"])


# ---------------------------------------------------------------------------
# Dashboard panels
# ---------------------------------------------------------------------------

def _lens_metric_panel(panel_id: str, title: str, index_id: str, field: str, x: int, y: int) -> dict:
    """Single-value metric panel using Lens."""
    return {
        "type": "lens",
        "gridData": {"x": x, "y": y, "w": 12, "h": 8, "i": panel_id},
        "panelIndex": panel_id,
        "embeddableConfig": {
            "title": title,
            "attributes": {
                "title": title,
                "visualizationType": "lnsMetric",
                "references": [{"id": index_id, "name": "indexpattern-datasource-layer-1", "type": "index-pattern"}],
                "state": {
                    "datasourceStates": {
                        "formBased": {
                            "layers": {
                                "layer1": {
                                    "columns": {
                                        "col1": {
                                            "label": title,
                                            "dataType": "number",
                                            "operationType": "max",
                                            "sourceField": field,
                                            "isBucketed": False,
                                        }
                                    },
                                    "columnOrder": ["col1"],
                                }
                            }
                        }
                    },
                    "visualization": {
                        "layerId": "layer1",
                        "layerType": "data",
                        "metricAccessor": "col1",
                    },
                },
            },
        },
    }


def _lens_timeseries_panel(
    panel_id: str, title: str, index_id: str, metric_value: str, x: int, y: int, w: int = 24, h: int = 15
) -> dict:
    """Line chart timeseries panel — filters by metric field value."""
    return {
        "type": "lens",
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": panel_id},
        "panelIndex": panel_id,
        "embeddableConfig": {
            "title": title,
            "attributes": {
                "title": title,
                "visualizationType": "lnsXY",
                "references": [{"id": index_id, "name": "indexpattern-datasource-layer-1", "type": "index-pattern"}],
                "state": {
                    "query": {"query": f'metric: "{metric_value}"', "language": "kuery"},
                    "datasourceStates": {
                        "formBased": {
                            "layers": {
                                "layer1": {
                                    "columns": {
                                        "col_x": {
                                            "label": "Date",
                                            "dataType": "date",
                                            "operationType": "date_histogram",
                                            "sourceField": "@timestamp",
                                            "isBucketed": True,
                                            "params": {"interval": "auto"},
                                        },
                                        "col_y": {
                                            "label": "Count",
                                            "dataType": "number",
                                            "operationType": "sum",
                                            "sourceField": "count",
                                            "isBucketed": False,
                                        },
                                    },
                                    "columnOrder": ["col_x", "col_y"],
                                }
                            }
                        }
                    },
                    "visualization": {
                        "legend": {"isVisible": True, "position": "bottom"},
                        "valueLabels": "hide",
                        "fittingFunction": "None",
                        "layers": [
                            {
                                "layerId": "layer1",
                                "accessors": ["col_y"],
                                "xAccessor": "col_x",
                                "layerType": "data",
                                "seriesType": "line",
                            }
                        ],
                    },
                },
            },
        },
    }


def _lens_bar_breakdown_panel(
    panel_id: str, title: str, index_id: str, breakdown_field: str,
    metric_filter: str, x: int, y: int, w: int = 24, h: int = 15
) -> dict:
    """Horizontal bar chart breaking down by a keyword field."""
    return {
        "type": "lens",
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": panel_id},
        "panelIndex": panel_id,
        "embeddableConfig": {
            "title": title,
            "attributes": {
                "title": title,
                "visualizationType": "lnsXY",
                "references": [{"id": index_id, "name": "indexpattern-datasource-layer-1", "type": "index-pattern"}],
                "state": {
                    "query": {"query": metric_filter, "language": "kuery"},
                    "datasourceStates": {
                        "formBased": {
                            "layers": {
                                "layer1": {
                                    "columns": {
                                        "col_x": {
                                            "label": breakdown_field,
                                            "dataType": "string",
                                            "operationType": "terms",
                                            "sourceField": breakdown_field,
                                            "isBucketed": True,
                                            "params": {"size": 10, "orderBy": {"type": "column", "columnId": "col_y"}, "orderDirection": "desc"},
                                        },
                                        "col_y": {
                                            "label": "Count",
                                            "dataType": "number",
                                            "operationType": "sum",
                                            "sourceField": "count",
                                            "isBucketed": False,
                                        },
                                    },
                                    "columnOrder": ["col_x", "col_y"],
                                }
                            }
                        }
                    },
                    "visualization": {
                        "legend": {"isVisible": True, "position": "right"},
                        "layers": [
                            {
                                "layerId": "layer1",
                                "accessors": ["col_y"],
                                "xAccessor": "col_x",
                                "layerType": "data",
                                "seriesType": "bar_horizontal",
                            }
                        ],
                    },
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# Dashboard definitions
# ---------------------------------------------------------------------------

def build_overview_dashboard() -> dict:
    idx = "glean-overview"
    panels = [
        _lens_metric_panel("p1", "Monthly Active Users",      idx, "monthly_active_users",       0,  0),
        _lens_metric_panel("p2", "Weekly Active Users",       idx, "weekly_active_users",        12,  0),
        _lens_metric_panel("p3", "Employee Count",            idx, "employee_count",             24,  0),
        _lens_metric_panel("p4", "Total Signups",             idx, "total_signups",              36,  0),
        _lens_timeseries_panel("p5",  "All Users DAU",              idx, "dau_all",       0, 8),
        _lens_timeseries_panel("p6",  "Search DAU",                 idx, "dau_search",    24, 8),
        _lens_timeseries_panel("p7",  "Assistant DAU",              idx, "dau_assistant", 0, 23),
        _lens_timeseries_panel("p8",  "Agents DAU",                 idx, "dau_agents",    24, 23),
        _lens_timeseries_panel("p9",  "Daily Searches Volume",      idx, "searches",      0, 38),
        _lens_timeseries_panel("p10", "Assistant Interactions",     idx, "assistant_interactions", 24, 38),
        _lens_timeseries_panel("p11", "Agent Runs",                 idx, "agent_runs",    0, 53),
    ]
    return {
        "attributes": {
            "title": "Glean — Platform Overview",
            "panels": json.dumps(panels),
            "timeFrom": "now-30d",
            "timeTo": "now",
            "refreshInterval": {"pause": True, "value": 0},
        }
    }


def build_assistant_dashboard() -> dict:
    idx = "glean-assistant"
    panels = [
        _lens_metric_panel("p1", "MAU (Assistant)", idx, "monthly_active_users", 0,  0),
        _lens_metric_panel("p2", "WAU (Assistant)", idx, "weekly_active_users",  12, 0),
        _lens_metric_panel("p3", "Total Signups",   idx, "total_signups",        24, 0),
        _lens_timeseries_panel("p4", "Daily Active Users",         idx, "dau",                   0,  8),
        _lens_timeseries_panel("p5", "Chat Messages",              idx, "chat_messages",          24, 8),
        _lens_timeseries_panel("p6", "AI Answers",                 idx, "ai_answers",             0,  23),
        _lens_timeseries_panel("p7", "Summarizations",             idx, "summarizations",         24, 23),
        _lens_timeseries_panel("p8", "Gleanbot Interactions",      idx, "gleanbot_interactions",  0,  38),
        _lens_timeseries_panel("p9", "Upvotes vs Downvotes",       idx, "upvotes",                24, 38),
    ]
    return {
        "attributes": {
            "title": "Glean — Assistant Analytics",
            "panels": json.dumps(panels),
            "timeFrom": "now-30d",
            "timeTo": "now",
            "refreshInterval": {"pause": True, "value": 0},
        }
    }


def build_agents_dashboard() -> dict:
    idx = "glean-agents"
    panels = [
        _lens_metric_panel("p1", "MAU (Agents)",       idx, "monthly_active_users", 0,  0),
        _lens_metric_panel("p2", "WAU (Agents)",       idx, "weekly_active_users",  12, 0),
        _lens_metric_panel("p3", "Shared Agents",      idx, "shared_agents_count",  24, 0),
        _lens_timeseries_panel("p4",  "Daily Agent Runs",      idx, "agent_runs",    0,  8),
        _lens_timeseries_panel("p5",  "Successful Runs",       idx, "runs_success",  24, 8),
        _lens_timeseries_panel("p6",  "Failed Runs",           idx, "runs_failed",   0,  23),
        _lens_timeseries_panel("p7",  "Paused Runs",           idx, "runs_paused",   24, 23),
        _lens_timeseries_panel("p8",  "Agent Upvotes",         idx, "upvotes",       0,  38),
        _lens_timeseries_panel("p9",  "Agent Downvotes",       idx, "downvotes",     24, 38),
        _lens_bar_breakdown_panel(
            "p10", "Top Agents by Usage", idx, "agentName",
            'doc_type: "agent_top"', 0, 53
        ),
        _lens_bar_breakdown_panel(
            "p11", "Usage by Department", idx, "department",
            'doc_type: "agent_dept_usage"', 24, 53
        ),
    ]
    return {
        "attributes": {
            "title": "Glean — Agents Analytics",
            "panels": json.dumps(panels),
            "timeFrom": "now-30d",
            "timeTo": "now",
            "refreshInterval": {"pause": True, "value": 0},
        }
    }


def create_dashboards() -> None:
    dashboards = [
        build_overview_dashboard(),
        build_assistant_dashboard(),
        build_agents_dashboard(),
    ]
    for d in dashboards:
        try:
            result = kibana_post("/api/saved_objects/dashboard", d)
            log.info("Created dashboard: %s (id=%s)", d["attributes"]["title"], result.get("id"))
        except requests.HTTPError:
            log.warning("Dashboard '%s' creation failed — may already exist.", d["attributes"]["title"])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("Setting up Kibana data views and dashboards...")
    create_data_views()
    create_dashboards()
    log.info("Kibana setup complete.")


if __name__ == "__main__":
    main()
