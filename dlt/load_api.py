from datetime import date, datetime, timedelta, timezone
from urllib import response
import dlt
import requests
from pathlib import Path
import os
from dotenv import load_dotenv


BASE_URL = "https://api.swedavia.se/flightinfo/v2"

load_dotenv()  # Load environment variables from .env file
API_KEY = os.getenv("SWEDAVIA_API_KEY")

IATA = [
    "ARN",
    "GOT",
    "MMX",
    "BMA",
    "LLA",
    "OSD",
    "UME",
    "KRN",
    "VBY",
    "RNB",
]

ENDPOINTS = [
    "arrivals",
    "departures",
]


def get_flight_date():
    # Returns the dates for:  2 days ago, 1 day ago

    dates = []

    for days_ago in range(2, 0, -1):
        flight_date = date.today() - timedelta(days=days_ago)
        dates.append(flight_date)

    return dates

# def get_flight_date():
#     dates = []
#     flight_date = date.today() - timedelta(days=1)
#     dates.append(flight_date)
#     return dates

def get_flights(IATA, endpoint, flight_date):
    # Get flight data from Swedavia API.
    url = f"{BASE_URL}/{IATA}/{endpoint}/{flight_date}"
    headers = {
        "accept": "application/json",
        "Ocp-Apim-Subscription-Key": API_KEY,
    }
    response = requests.get(
        url,
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


@dlt.resource(write_disposition="append")
def get_flight_data():
    # Extract flight data for the previous days.
    fetched_at = datetime.now(timezone.utc).isoformat()
    dates = get_flight_date()
    for flight_date in dates:
        print(f"Getting flights for {flight_date}")
        for airport in IATA:
            for endpoint in ENDPOINTS:
                print(f"  {airport} - {endpoint}")
                data = get_flights(airport, endpoint, flight_date)
                for flight in data.get("flights", []):
                    flight["direction"] = endpoint          # "arrivals" / "departures"
                    flight["query_date"] = flight_date.isoformat()
                    flight["fetched_at"] = fetched_at
                    yield flight


def run_pipeline():
    pipeline = dlt.pipeline(
        pipeline_name="flight_data",
        destination="snowflake",
        dataset_name="raw",
    )
    load_info = pipeline.run(get_flight_data(),table_name="flights",)
    print(load_info)


if __name__ == "__main__":
    working_directory = Path(__file__).parent
    os.chdir(working_directory)

    run_pipeline()