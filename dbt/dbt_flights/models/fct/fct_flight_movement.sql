with src_flights as (select * from {{ ref('src_flights') }})

select
    {{ dbt_utils.generate_surrogate_key(['direction', 'flight_id', 'airport_iata', 'scheduled_utc']) }}
                                                                        as flight_movement_key,
    direction,
    flight_id,
    to_number(to_char(scheduled_utc::date, 'YYYYMMDD'))                 as scheduled_date_key,
    {{ dbt_utils.generate_surrogate_key(['airport_iata']) }}            as airport_key,
    {{ dbt_utils.generate_surrogate_key(['other_airport_iata']) }}      as other_airport_key,
    {{ dbt_utils.generate_surrogate_key(['airline_icao']) }}            as airline_key,
    {{ dbt_utils.generate_surrogate_key(['status_code']) }}             as status_key,
    {{ dbt_utils.generate_surrogate_key(['di_code']) }}                 as di_key,
    scheduled_utc,
    estimated_utc,
    actual_utc,
    datediff('minute', scheduled_utc, actual_utc)                       as delay_minutes,
    datediff('minute', scheduled_utc, actual_utc) > 15                  as is_delayed,
    fetched_at
from src_flights