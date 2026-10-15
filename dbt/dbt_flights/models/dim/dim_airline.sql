with src_flights as (select * from {{ ref('src_flights') }}),
src_airline_wiki as (select * from {{ ref('src_airline_wiki') }}),

airlines as (
    select
        airline_iata,
        max(airline_icao) as airline_icao,
        max(airline_name) as airline_name
    from src_flights
    group by airline_iata
)

select
    {{ dbt_utils.generate_surrogate_key(['a.airline_iata']) }}  as airline_key,
    a.airline_iata                                              as iata_code,
    a.airline_icao                                              as icao_code,
    coalesce(w.airline_name, a.airline_name)                    as name,
    w.callsign,
    w.country
from airlines a
left join src_airline_wiki w
    on a.airline_icao = w.icao_code
qualify row_number() over (
    partition by a.airline_iata
    order by (w.iata_code = a.airline_iata) desc nulls last, w.is_defunct
) = 1