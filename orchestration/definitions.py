import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # projektets rotmapp
sys.path.insert(0, str(ROOT))

import dagster as dg
import dlt
from dagster_dlt import DagsterDltResource, dlt_assets
from dotenv import load_dotenv

from data_extract_load.load_api import flights_source
from data_extract_load.load_wikipedia_csv import wikipedia_source

load_dotenv(ROOT / ".env")


def snowflake_destination():
    return dlt.destinations.snowflake(
        credentials={
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "username": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "host": os.getenv("SNOWFLAKE_ACCOUNT"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
        }
    )


dlt_resource = DagsterDltResource()


# --- Swedavia (API) ---
@dlt_assets(
    dlt_source=flights_source(),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="flight_data",
        dataset_name="raw",
        destination=snowflake_destination(),
    ),
)
def dlt_flights(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


# --- Wikipedia (CSV) ---
@dlt_assets(
    dlt_source=wikipedia_source(),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="wikipedia",
        dataset_name="raw",
        destination=snowflake_destination(),
    ),
)
def dlt_wikipedia(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


job_flights = dg.define_asset_job(
    "job_flights",
    selection=dg.AssetSelection.keys("dlt_flights_source_flights_resource"),
)

job_wikipedia = dg.define_asset_job(
    "job_wikipedia",
    selection=dg.AssetSelection.keys(
        "dlt_wikipedia_source_wiki_airlines",
        "dlt_wikipedia_source_wiki_airports",
    ),
)

schedule_flights = dg.ScheduleDefinition(
    job=job_flights,
    cron_schedule="0 12 * * *",  # kl 12:00 varje dag
    execution_timezone="Europe/Stockholm",
)

defs = dg.Definitions(
    assets=[dlt_flights, dlt_wikipedia],
    resources={"dlt": dlt_resource},
    jobs=[job_flights, job_wikipedia],
    schedules=[schedule_flights],
)

# från rot: uv run dagster dev -f orchestration/definitions.py