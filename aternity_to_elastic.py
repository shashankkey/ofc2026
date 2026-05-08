"""
Aternity BUSINESS_ACTIVITIES_HOURLY → Elasticsearch Data Stream Ingestion

Pulls hourly business activity data from Aternity's OData REST API
and ingests into an Elasticsearch data stream using bulk operations.

Designed to run as a cron job — stateless, pulls last N hours each run.

Usage:
    python aternity_to_elastic.py                # Pull last 2 hours (default)
    python aternity_to_elastic.py --hours 48     # Pull last 48 hours
    python aternity_to_elastic.py --dry-run      # Fetch from Aternity but don't ingest

Cron example (run every hour):
    0 * * * * /usr/bin/python3 /path/to/aternity_to_elastic.py >> /var/log/aternity_ingestion.log 2>&1
"""

import os
import sys
import json
import logging
import argparse
import hashlib
from datetime import datetime, timezone

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

ATERNITY_BASE_URL = os.getenv("ATERNITY_BASE_URL", "").rstrip("/")
ATERNITY_USERNAME = os.getenv("ATERNITY_USERNAME", "")
ATERNITY_PASSWORD = os.getenv("ATERNITY_PASSWORD", "")

ELASTIC_URL = os.getenv("ELASTIC_URL", "https://localhost:9200")
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "")
ELASTIC_VERIFY_SSL = os.getenv("ELASTIC_VERIFY_SSL", "true").lower() == "true"

LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "2"))
BULK_BATCH_SIZE = int(os.getenv("BULK_BATCH_SIZE", "500"))
DATA_STREAM_NAME = os.getenv("DATA_STREAM_NAME", "metrics-aternity.business_activities-default")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Fields to select from the Aternity OData API
ODATA_SELECT_FIELDS = [
    # Attributes (Dimensions)
    "Timeframe",
    "Application_Name",
    "Managed_Application",
    "Activity_Name",
    "Activity_Type",
    "Username",
    "Device_Name",
    "Device_Type",
    "OS_Name",
    "OS_Version",
    "Location_City",
    "Location_Country",
    "Location_State",
    "Department",
    "Detection_Status",
    "Connection_Type",
    "Process_Name",
    # Measurements (Metrics)
    "Activity_Response_Avg",
    "Activity_Response_Max",
    "Activity_Response_Min",
    "Activity_Score",
    "Volume",
    "Wait_Time",
    "Hang_Time",
    "Activity_Client_Time_Avg",
    "Activity_Network_Time_Avg",
    "Activity_Backend_Time_Avg",
    "Activity_Infra_Time_Avg",
    # Resource consumption at time of activity
    "HRC_CPU_Avg",
    "HRC_Memory_Avg",
    "PRC_CPU_Avg",
    "PRC_Memory_Avg",
]

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("aternity_ingestion")


# ---------------------------------------------------------------------------
# Aternity OData client
# ---------------------------------------------------------------------------
class AternityClient:
    """Fetches data from Aternity OData REST API."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def fetch_business_activities_hourly(
        self,
        lookback_hours: int = 2,
    ) -> list[dict]:
        """
        Fetch BUSINESS_ACTIVITIES_HOURLY data from Aternity.

        Args:
            lookback_hours: How many hours of data to pull.

        Returns:
            List of activity records (dicts).
        """
        endpoint = f"{self.base_url}/BUSINESS_ACTIVITIES_HOURLY"

        # Build $select
        select = ",".join(ODATA_SELECT_FIELDS)

        # Build $filter — map to Aternity's relative_time() buckets
        if lookback_hours <= 1:
            relative = "last_1_hour"
        elif lookback_hours <= 2:
            relative = "last_2_hours"
        elif lookback_hours <= 4:
            relative = "last_4_hours"
        elif lookback_hours <= 8:
            relative = "last_8_hours"
        elif lookback_hours <= 24:
            relative = "last_24_hours"
        elif lookback_hours <= 48:
            relative = "last_2_days"
        elif lookback_hours <= 168:
            relative = "last_week"
        else:
            relative = "last_month"
        filter_expr = f"relative_time({relative})"

        params = {
            "$select": select,
            "$filter": filter_expr,
            "$format": "json",
        }

        all_records = []
        url = endpoint

        logger.info(f"Fetching from Aternity: {endpoint}")
        logger.info(f"  $filter = {filter_expr}")
        logger.debug(f"  $select = {select}")

        page = 1
        while url:
            try:
                resp = self.session.get(
                    url,
                    params=params if page == 1 else None,
                    timeout=120,
                )
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error(f"Aternity API HTTP error: {e}")
                logger.error(f"Response body: {resp.text[:1000]}")
                raise
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Cannot connect to Aternity server: {e}")
                raise
            except requests.exceptions.Timeout:
                logger.error("Aternity API request timed out (120s)")
                raise

            data = resp.json()

            # OData v2 wraps in d.results; OData v4 uses value
            if "d" in data and "results" in data["d"]:
                records = data["d"]["results"]
            elif "value" in data:
                records = data["value"]
            else:
                records = data.get("d", [])
                if isinstance(records, dict):
                    records = [records]

            all_records.extend(records)
            logger.info(f"  Page {page}: fetched {len(records)} records (total: {len(all_records)})")

            # OData pagination
            next_link = None
            if "d" in data and "__next" in data["d"]:
                next_link = data["d"]["__next"]
            elif "@odata.nextLink" in data:
                next_link = data["@odata.nextLink"]

            url = next_link
            page += 1

        logger.info(f"Total records fetched from Aternity: {len(all_records)}")
        return all_records


# ---------------------------------------------------------------------------
# Document transformation
# ---------------------------------------------------------------------------
def generate_doc_id(record: dict) -> str:
    """
    Generate a deterministic document ID from the record's natural key.
    Data streams will reject duplicates (version_conflict_engine_exception)
    if the same record is ingested again on overlapping cron runs.
    """
    key = "|".join([
        str(record.get("Timeframe", "")),
        str(record.get("Application_Name", "")),
        str(record.get("Activity_Name", "")),
        str(record.get("Username", "")),
        str(record.get("Device_Name", "")),
    ])
    return hashlib.sha256(key.encode()).hexdigest()[:20]



def parse_aternity_datetime(value) -> str | None:
    """
    Parse Aternity datetime into ISO 8601.
    Handles OData /Date(epoch_ms)/ format and plain ISO strings.
    """
    if not value:
        return None
    if isinstance(value, str) and value.startswith("/Date("):
        try:
            ms = int(value.replace("/Date(", "").replace(")/", "").split("+")[0].split("-")[0])
            dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
            return dt.isoformat()
        except (ValueError, OverflowError):
            return value
    return value


def safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def transform_record(raw: dict) -> dict:
    """
    Transform a raw Aternity OData record into a clean Elasticsearch document.
    Adds @timestamp required by data streams.
    """
    timeframe = parse_aternity_datetime(raw.get("Timeframe"))

    doc = {
        # @timestamp is REQUIRED for data streams
        "@timestamp": timeframe or datetime.now(timezone.utc).isoformat(),

        # Attributes (Dimensions)
        "timeframe": timeframe,
        "application_name": raw.get("Application_Name"),
        "managed_application": raw.get("Managed_Application"),
        "activity_name": raw.get("Activity_Name"),
        "activity_type": raw.get("Activity_Type"),
        "username": raw.get("Username"),
        "device_name": raw.get("Device_Name"),
        "device_type": raw.get("Device_Type"),
        "os_name": raw.get("OS_Name"),
        "os_version": raw.get("OS_Version"),
        "location_city": raw.get("Location_City"),
        "location_country": raw.get("Location_Country"),
        "location_state": raw.get("Location_State"),
        "department": raw.get("Department"),
        "detection_status": raw.get("Detection_Status"),
        "connection_type": raw.get("Connection_Type"),
        "process_name": raw.get("Process_Name"),

        # Measurements (Metrics)
        "activity_response_avg": safe_float(raw.get("Activity_Response_Avg")),
        "activity_response_max": safe_float(raw.get("Activity_Response_Max")),
        "activity_response_min": safe_float(raw.get("Activity_Response_Min")),
        "activity_score": safe_float(raw.get("Activity_Score")),
        "volume": safe_int(raw.get("Volume")),
        "wait_time": safe_float(raw.get("Wait_Time")),
        "hang_time": safe_float(raw.get("Hang_Time")),
        "activity_client_time_avg": safe_float(raw.get("Activity_Client_Time_Avg")),
        "activity_network_time_avg": safe_float(raw.get("Activity_Network_Time_Avg")),
        "activity_backend_time_avg": safe_float(raw.get("Activity_Backend_Time_Avg")),
        "activity_infra_time_avg": safe_float(raw.get("Activity_Infra_Time_Avg")),

        # Resource consumption at time of activity
        "hrc_cpu_avg": safe_float(raw.get("HRC_CPU_Avg")),
        "hrc_memory_avg": safe_float(raw.get("HRC_Memory_Avg")),
        "prc_cpu_avg": safe_float(raw.get("PRC_CPU_Avg")),
        "prc_memory_avg": safe_float(raw.get("PRC_Memory_Avg")),

        # Enrichment metadata
        "data_source": "aternity",
        "data_entity": "business_activities_hourly",
    }

    # Remove keys with None values
    return {k: v for k, v in doc.items() if v is not None}


# ---------------------------------------------------------------------------
# Elasticsearch ingestion
# ---------------------------------------------------------------------------
class ElasticIngester:
    """Manages Elasticsearch connection and bulk ingestion into a data stream."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        data_stream: str = "metrics-aternity.business_activities-default",
    ):
        self.data_stream = data_stream

        self.es = Elasticsearch(
            url,
            basic_auth=(username, password),
            verify_certs=verify_ssl,
            ssl_show_warn=verify_ssl,
            request_timeout=60,
        )

        # Verify connection
        info = self.es.info()
        logger.info(
            f"Connected to Elasticsearch {info['version']['number']} "
            f"cluster: {info['cluster_name']}"
        )

    def ingest(self, records: list[dict], batch_size: int = 500) -> dict:
        """Bulk ingest transformed records into the data stream."""
        if not records:
            logger.info("No records to ingest")
            return {"success": 0, "errors": 0}

        def generate_actions():
            for record in records:
                doc = transform_record(record)
                doc_id = generate_doc_id(record)
                yield {
                    "_op_type": "create",
                    "_index": self.data_stream,
                    "_id": doc_id,
                    **doc,
                }

        success_count = 0
        error_count = 0

        batch = []
        for action in generate_actions():
            batch.append(action)
            if len(batch) >= batch_size:
                s, e = self._bulk_send(batch)
                success_count += s
                error_count += e
                batch = []

        if batch:
            s, e = self._bulk_send(batch)
            success_count += s
            error_count += e

        logger.info(f"Ingestion complete: {success_count} success, {error_count} errors")
        return {"success": success_count, "errors": error_count}

    def _bulk_send(self, actions: list[dict]) -> tuple[int, int]:
        """Send a batch via bulk API. Returns (success, error) counts."""
        try:
            success, errors = helpers.bulk(
                self.es,
                actions,
                raise_on_error=False,
                raise_on_exception=False,
                stats_only=False,
            )

            if isinstance(errors, list) and errors:
                # Separate duplicate rejections from real errors
                real_errors = [
                    e for e in errors
                    if not (isinstance(e, dict) and
                            e.get("create", {}).get("error", {}).get("type")
                            == "version_conflict_engine_exception")
                ]
                dup_count = len(errors) - len(real_errors)
                if dup_count:
                    logger.info(f"  Skipped {dup_count} duplicate records")
                if real_errors:
                    for err in real_errors[:3]:
                        logger.error(f"  Bulk error: {json.dumps(err, indent=2)[:500]}")
                    return success, len(real_errors)
                return success + dup_count, 0

            logger.debug(f"  Bulk sent: {success} docs")
            return success, 0

        except Exception as e:
            logger.error(f"Bulk API exception: {e}")
            return 0, len(actions)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run_pipeline(lookback_hours: int | None = None, dry_run: bool = False) -> None:
    """
    Main pipeline — stateless, designed for cron execution:
    1. Fetch last N hours of data from Aternity
    2. Ingest into Elasticsearch data stream
    """

    # Validate config
    if not ATERNITY_BASE_URL:
        logger.error("ATERNITY_BASE_URL is not set in .env")
        sys.exit(1)
    if not ATERNITY_USERNAME or not ATERNITY_PASSWORD:
        logger.error("ATERNITY_USERNAME / ATERNITY_PASSWORD is not set in .env")
        sys.exit(1)
    if not dry_run and not ELASTIC_PASSWORD:
        logger.error("ELASTIC_PASSWORD is not set in .env")
        sys.exit(1)

    # Initialize Aternity client
    aternity = AternityClient(ATERNITY_BASE_URL, ATERNITY_USERNAME, ATERNITY_PASSWORD)

    # Initialize Elasticsearch (unless dry run)
    es_ingester = None
    if not dry_run:
        es_ingester = ElasticIngester(
            url=ELASTIC_URL,
            username=ELASTIC_USERNAME,
            password=ELASTIC_PASSWORD,
            verify_ssl=ELASTIC_VERIFY_SSL,
            data_stream=DATA_STREAM_NAME,
        )

    # Fetch from Aternity
    hours = lookback_hours or LOOKBACK_HOURS
    logger.info(f"Pulling last {hours} hours of data")

    records = aternity.fetch_business_activities_hourly(lookback_hours=hours)

    if not records:
        logger.info("No records from Aternity. Nothing to ingest.")
        return

    # Ingest or dry-run
    if dry_run:
        logger.info(f"[DRY RUN] Would ingest {len(records)} records. Samples:")
        for r in records[:3]:
            transformed = transform_record(r)
            logger.info(f"  {json.dumps(transformed, indent=2)[:500]}")
    else:
        result = es_ingester.ingest(records, batch_size=BULK_BATCH_SIZE)
        logger.info(f"Pipeline result: {result}")

    logger.info("Run complete.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Aternity BUSINESS_ACTIVITIES_HOURLY → Elasticsearch Data Stream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python aternity_to_elastic.py                # Pull last 2 hours (default)
  python aternity_to_elastic.py --hours 48     # Pull last 48 hours
  python aternity_to_elastic.py --dry-run      # Test without ingesting

Cron (every hour):
  0 * * * * /usr/bin/python3 /opt/aternity/aternity_to_elastic.py
        """,
    )
    parser.add_argument(
        "--hours", type=int, default=None,
        help="Override lookback hours (default: LOOKBACK_HOURS from .env)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch from Aternity but don't ingest into Elasticsearch",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Aternity → Elasticsearch Ingestion Pipeline")
    logger.info("=" * 60)
    logger.info(f"  Aternity URL : {ATERNITY_BASE_URL}")
    logger.info(f"  Elastic URL  : {ELASTIC_URL}")
    logger.info(f"  Data Stream  : {DATA_STREAM_NAME}")
    logger.info(f"  Dry Run      : {args.dry_run}")
    logger.info("=" * 60)

    run_pipeline(lookback_hours=args.hours, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
