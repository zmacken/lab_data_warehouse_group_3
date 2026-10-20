import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # projektets rotmapp
sys.path.insert(0, str(ROOT))  # gör att data_extract_load kan importeras

import dagster as dg
import dlt
from dagster_dlt import DagsterDltResource, dlt_assets
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dotenv import load_dotenv

from data_extract_load.load_api import flights_source
from data_extract_load.load_wikipedia_csv import wikipedia_source

load_dotenv(ROOT / ".env")  # läser Snowflake-uppgifter från .env


def snowflake_destination():
    # Snowflake-mål för dlt, används av båda pipelines
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


dlt_resource = DagsterDltResource()  # kör dlt-kod i Dagster


# ==================== #
#    Swedavia Asset    #
# ==================== #
@dlt_assets(
    dlt_source=flights_source(),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="flight_data",
        dataset_name="raw",
        destination=snowflake_destination(),
    ),
)
def dlt_flights(context: dg.AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)  # hämtar data och laddar till Snowflake


# ==================== #
#    Wikipedia Asset   #
# ==================== #
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


# ==================== #
#       dbt Asset      #
# ==================== #
# kräver att 'dbt deps' körts i dbt-projektet
dbt_project_directory = ROOT / "dbt/dbt_flights"
profiles_dir = Path.home() / ".dbt"  # här ligger profiles.yml

dbt_project = DbtProject(
    project_dir=dbt_project_directory,
    profiles_dir=profiles_dir,
)

dbt_resource = DbtCliResource(project_dir=dbt_project)  # kör dbt-kommandon

dbt_project.prepare_if_dev()  # skapar manifest.json (modeller och beroenden)


@dbt_assets(manifest=dbt_project.manifest_path)  # en asset per dbt-modell
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()  # stream = live i UI:t


# ==================== #
#         Jobs         #
# ==================== #
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

job_dbt = dg.define_asset_job(
    "job_dbt",
    selection=dg.AssetSelection.assets(dbt_models),  # alla dbt-modeller
)

# ==================== #
#       Schedule       #
# ==================== #
schedule_flights = dg.ScheduleDefinition(
    job=job_flights,
    cron_schedule="0 12 * * *",  # kl 12:00 varje dag
    execution_timezone="Europe/Stockholm",
)

# ==================== #
#        Sensors       #
# ==================== #
# startar dbt-jobbet när flygdatan har laddats klart
@dg.asset_sensor(
    asset_key=dg.AssetKey("dlt_flights_source_flights_resource"),
    job=job_dbt,
)
def dlt_flights_sensor():
    yield dg.RunRequest()


defs = dg.Definitions(
    assets=[dlt_flights, dlt_wikipedia, dbt_models],
    resources={
        "dlt": dlt_resource,
        "dbt": dbt_resource,
    },
    jobs=[job_flights, job_wikipedia, job_dbt],
    schedules=[schedule_flights],
    sensors=[dlt_flights_sensor],
)

# från rot: uv run dagster dev -f orchestration/definitions.py