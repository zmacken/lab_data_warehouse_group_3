import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import dlt
import requests 
from dotenv import load_dotenv

# Rotmappen räknas ut från filens plats, så .env hittas oavsett varifrån du kör
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("SWEDAVIA_API_KEY")
BASE_URL = "https://api.swedavia.se/flightinfo/v2"

IATA = os.getenv(
    "SWEDAVIA_AIRPORTS",
    "ARN,GOT,MMX,BMA,LLA,OSD,UME,KRN,VBY,RNB",
).split(",")
ENDPOINTS = ["arrivals", "departures"]


def get_flight_dates(days_back=3):
    return [date.today() - timedelta(days=offset) for offset in range(days_back - 1, -1,-1)]


def get_flights(airport, endpoint, flight_date):
    url = f"{BASE_URL}/{airport}/{endpoint}/{flight_date}"
    headers = {
        "accept": "application/json",
        "Ocp-Apim-Subscription-Key": API_KEY,
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


@dlt.resource(table_name="flights", write_disposition="append")
def flights_resource():
    print(f"Airports: {IATA}")  # test
    # Tidsstämpel för just den här hämtningen
    fetched_at = datetime.now(timezone.utc).isoformat()
    for flight_date in get_flight_dates():
        for airport in IATA:
            for endpoint in ENDPOINTS:
                print(f"  {airport} - {endpoint}")
                data = get_flights(airport, endpoint, flight_date)
                for flight in data.get("flights", []):
                    flight["direction"] = endpoint
                    flight["airport_iata"] = airport
                    flight["query_date"] = flight_date.isoformat()
                    flight["fetched_at"] = fetched_at
                    yield flight


# Dagster fungerar bara med dlt source, inte med dlt resource
@dlt.source
def flights_source():
    return flights_resource()