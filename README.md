# Flight Punctuality Analytics

Proof of concept för en modern data stack som analyserar flygförseningar på svenska flygplatser (Swedavia).
Fokus: antal försenade ankomster och avgångar, uppdelat på flygbolag, flygplats och datum.

## Teknikstack

| Steg | Verktyg |
|---|---|
| Extract & load | dlt |
| Datalager | Snowflake |
| Transformering | dbt Core |
| Orkestrering | Dagster |
| Dashboard | Streamlit |

## Dataflöde

```
Swedavia FlightInfo API ─┐
                         ├─ dlt ─► Snowflake RAW ─► dbt ─► STAGING (dim/fct) ─► MARTS ─► Streamlit
Wikipedia (CSV) ─────────┘
```

1. **Extract/load:** `data_extract_load/` hämtar ankomster och avgångar för alla 10 Swedavia-flygplatser och laddar dem till schemat `RAW`. Wikipedia-data (flygbolag och flygplatser) scrapas med `scraping/scrape_wikipedia.py` och laddas från CSV.
2. **Transformering:** dbt rensar och avduplicerar datan (`src_*`) och bygger en stjärnmodell (`dim_*`, `fct_flight_movement`). Vyn `mart_flight_delays` i schemat `MARTS` är det dashboarden läser.
3. **Orkestrering:** Dagster kör dlt-laddningen enligt schema och startar dbt när flygdatan har laddats.
4. **Dashboard:** Streamlit läser från `MARTS`.

## Datamodell

Stjärnmodellen finns i `dimensional_modeling/model.dbml` (öppna i [dbdiagram.io](https://dbdiagram.io)).

- **Fakta:** `fct_flight_movement` – en rad per flygrörelse (ankomst eller avgång).
- **Dimensioner:** `dim_date`, `dim_airport` (används två gånger: aktuell och motpartens flygplats), `dim_airline`, `dim_flight_status`, `dim_di_indicator`.
- **Försenat flyg:** faktisk tid är mer än 15 minuter efter planerad tid.

## Snowflake-rättigheter

Skripten i `snowflake_setup/` körs i ordningen: `setup_warehouse.sql`, `setup_database.sql`, `setup_roles.sql`, `setup_user.sql`.
(`setup_user.sql` ligger inte i git eftersom den innehåller lösenord – skapa den själv.)

| Roll | Används av | Rättigheter |
|---|---|---|
| `LOADER` | dlt | Skriva i `RAW` |
| `TRANSFORMER` | dbt | Läsa `RAW`, skriva i `STAGING` och `MARTS` |
| `REPORTER` | Streamlit | Läsa `MARTS` |
| `ENGINEER` | Teamet (manuellt) | Ärver de tre ovan |

## Köra projektet lokalt

Förutsättningar: Python 3.12, [uv](https://docs.astral.sh/uv/), ett Snowflake-konto och en Swedavia API-nyckel.

```bash
# 1. Installera beroenden
uv sync

# 2. Skapa .env i projektets rot (lägg ALDRIG hemligheter i git)
SWEDAVIA_API_KEY=...
SNOWFLAKE_ACCOUNT=...
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_ROLE=LOADER
SNOWFLAKE_WAREHOUSE=FLIGHTDATA_WH
SNOWFLAKE_DATABASE=FLIGHTDATA_DB

# 3. dbt-profil: kopiera profiles.yml till ~/.dbt/ och installera paket
cp profiles.yml ~/.dbt/profiles.yml
cd dbt/dbt_flights && uv run dbt deps && cd ../..

# 4. Starta Dagster och kör jobben i UI:t (http://localhost:3000)
uv run dagster dev -f orchestration/definitions.py

# 5. Starta dashboarden (kräver dashboard/.streamlit/secrets.toml)
uv run streamlit run dashboard/app.py
```

I Dagster: kör `job_wikipedia` en gång, därefter `job_flights`. `job_dbt` startas automatiskt när flygdatan är laddad.

## Docker

```bash
docker compose up --build
```

- Dagster: http://localhost:3000
- Streamlit: http://localhost:8501
`

## Team

Hannah Zemack, Filip Farley, Julius Fält Skoglund, Anton Engström


## LLM

LLM har använts till delar av kod men inte för hel kodstruktur. 