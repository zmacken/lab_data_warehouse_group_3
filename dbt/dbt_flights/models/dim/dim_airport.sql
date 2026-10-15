with src_flights as (select * from {{ ref('src_flights') }}),
src_airline_wiki as (select * from {{ ref('src_airline_wiki') }}),

airlines as (
    select
        airline_iata                    as iata_code,
        max(airline_icao)               as icao_code,
        max(airline_name)               as name
    from src_flights
    group by airline_iata
)

select
    {{ dbt_utils.generate_surrogate_key(['a.iata_code']) }}  as airline_key,
    a.iata_code,
    a.icao_code,
    coalesce(w.airline_name, a.name)                         as name,
    w.callsign,
    w.country
from airlines a
left join src_airline_wiki w
    on a.iata_code = w.iata_code
and a.icao_code = w.icao_code
qualify row_number() over (
    partition by a.iata_code
    order by w.is_defunct, w.airline_name
) = 1