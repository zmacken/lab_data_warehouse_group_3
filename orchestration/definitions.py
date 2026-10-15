import os
from pathlib import Path

import dagster as dg
import dlt
from dagster_dlt import DagsterDltResource, dlt_assets
from dotenv import load_dotenv
from data_extract_load.load_api import flights_source

ROOT = Path(__file__).resolve().parent.parent  # projektets rotmapp
load_dotenv(ROOT / ".env")

dlt_resource = DagsterDltResource()


@dlt_assets(
    dlt_source=flights_source(),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="flight_data",
        dataset_name="raw",
        destination=dlt.destinations.snowflake(
            credentials={
                "database": os.getenv("SNOWFLAKE_DATABASE"),
                "username": os.getenv("SNOWFLAKE_USER"),
                "password": os.getenv("SNOWFLAKE_PASSWORD"),
                "host": os.getenv("SNOWFLAKE_ACCOUNT"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
                "role": os.getenv("SNOWFLAKE_ROLE"),
            }
        ),
    ),
)
def dlt_load(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


job_dlt = dg.define_asset_job(
    "job_dlt",
    selection=dg.AssetSelection.keys("dlt_flights_source_flights_resource"),
)

schedule_dlt = dg.ScheduleDefinition(
    job=job_dlt,
    cron_schedule="0 12 * * *",  # kl 12:00 varje dag
    execution_timezone="Europe/Stockholm",
)

defs = dg.Definitions(
    assets=[dlt_load],
    resources={"dlt": dlt_resource},
    jobs=[job_dlt],
    schedules=[schedule_dlt],
)