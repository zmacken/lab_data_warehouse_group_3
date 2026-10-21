import pandas as pd
from pathlib import Path

Path("data").mkdir(exist_ok=True)
opts = {"User-Agent": "examensarbete-scraper/1.0 (mail@mail.se)"}

# airline codes
airlines = pd.read_html(
    "https://en.wikipedia.org/wiki/List_of_airline_codes",
    storage_options=opts,
)[0]
airlines.to_csv("data/iata_airlines.csv", index=False)

# international airports
airports = pd.concat(
    pd.read_html(
        "https://en.wikipedia.org/wiki/List_of_international_airports_by_country",
        match="IATA",
        storage_options=opts,
    ),
    ignore_index=True,
)[["IATA Code", "Location", "Airport"]]
airports.to_csv("data/international_airports.csv", index=False)

print(airlines.shape, airports.shape)