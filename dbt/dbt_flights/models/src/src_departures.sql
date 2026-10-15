with flights as (
    select * from {{ source('swedavia', 'flights') }}
    where direction = 'departures'
)

select
    'D'                                                  as direction,
    flight_id,
    flight_leg_identifier__departure_airport_iata        as airport_iata,
    flight_leg_identifier__departure_airport_icao        as airport_icao,
    flight_leg_identifier__arrival_airport_iata          as other_airport_iata,
    flight_leg_identifier__arrival_airport_icao          as other_airport_icao,
    arrival_airport_swedish                              as other_airport_name_sv,
    arrival_airport_english                              as other_airport_name_en,
    airline_operator__iata                               as airline_iata,
    airline_operator__icao                               as airline_icao,
    airline_operator__name                               as airline_name,
    upper(trim(location_and_status__flight_leg_status))  as status_code,
    location_and_status__flight_leg_status_swedish       as status_text_sv,
    location_and_status__flight_leg_status_english       as status_text_en,
    upper(trim(di_indicator))                            as di_code,
    convert_timezone('UTC', departure_time__scheduled_utc)::timestamp_ntz as scheduled_utc,
    convert_timezone('UTC', departure_time__estimated_utc)::timestamp_ntz as estimated_utc,
    convert_timezone('UTC', departure_time__actual_utc)::timestamp_ntz    as actual_utc,
    fetched_at
from flights
qualify row_number() over (
    partition by flight_id, airport_iata, scheduled_utc
    order by fetched_at desc
) = 1