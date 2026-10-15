#Just remade from the old one to take variables instead
import os
from pathlib import Path
import dlt


def run_pipeline(pipeline_name, make_data, table_name=None, dataset_name="raw", destination="snowflake", refresh=None):
    os.chdir(Path(__file__).parent)
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=destination,
        dataset_name=dataset_name,
    )
    load_info = pipeline.run(make_data(), table_name=table_name, refresh=refresh)
    print(load_info)
    return load_info