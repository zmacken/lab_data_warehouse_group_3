from datetime import date, timedelta
import dlt
import requests
from pathlib import Path
import os


BASE_URL = "https://api.swedavia.se/flightinfo/v2"
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
    "VSB",
    "RNB",
]

ENDPOINTS = [
    "arrivals",
    "departures",
]


def get_flight_date():
    # Returns the dates for: 3 days ago, 2 days ago, 1 day ago

    dates = []

    for days_ago in range(3, 0, -1):
        flight_date = date.today() - timedelta(days=days_ago)
        dates.append(flight_date)

    return dates


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


@dlt.resource(write_disposition="replace")
def get_flight_data():
    # Extract flight data for the previous 3 days.
    dates = get_flight_date()
    for flight_date in dates:
        print(f"Getting flights for {flight_date}")
        for airport in IATA:
            for endpoint in ENDPOINTS:
                print(
                    f"  {airport} - {endpoint}"
                )
                data = get_flights(
                    airport,
                    endpoint,
                    flight_date,
                )
                for flight in data["hits"]:
                    yield flight


def run_pipeline():
    pipeline = dlt.pipeline(
        pipeline_name="flight_data",
        destination="snowflake",
        dataset_name="staging",
    )
    load_info = pipeline.run(get_flight_data(),table_name="flights",)
    print(load_info)


if __name__ == "__main__":
    working_directory = Path(__file__).parent
    os.chdir(working_directory)

    run_pipeline()