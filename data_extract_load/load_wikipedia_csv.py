from pathlib import Path

import dlt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "scraping" / "data"


def csv_rows(filename):
    df = pd.read_csv(DATA_DIR / filename)
    return df.astype(object).where(df.notna(), None).to_dict("records")  # tomt -> NULL


@dlt.resource(name="wiki_airlines", write_disposition="replace")
def wiki_airlines():
    yield from csv_rows("iata_airlines.csv")


@dlt.resource(name="wiki_airports", write_disposition="replace")
def wiki_airports():
    yield from csv_rows("international_airports.csv")


@dlt.source
def wikipedia_source():
    return wiki_airlines(), wiki_airports()