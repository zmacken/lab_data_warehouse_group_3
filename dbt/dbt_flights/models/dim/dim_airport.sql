with src_flights as (select * from {{ ref('src_flights') }}),
src_airport_wiki as (select * from {{ ref('src_airport_wiki') }}),

airports_from_flights as (
    select
        airport_iata                    as iata_code,
        airport_icao                    as icao_code,
        cast(null as varchar)           as name_sv,
        cast(null as varchar)           as name_en,
        true                            as is_swedavia_airport
    from src_flights

    union all

    select
        other_airport_iata,
        other_airport_icao,
        other_airport_name_sv,
        other_airport_name_en,
        false
    from src_flights
),

airports_agg as (
    select
        iata_code,
        max(icao_code)                  as icao_code,
        max(name_sv)                    as name_sv,
        max(name_en)                    as name_en,
        boolor_agg(is_swedavia_airport) as is_swedavia_airport
    from airports_from_flights
    where iata_code is not null
    group by iata_code
)

select
    {{ dbt_utils.generate_surrogate_key(['a.iata_code']) }}  as airport_key,
    a.iata_code,
    a.icao_code,
    a.name_sv,
    coalesce(w.airport_name, a.name_en)                      as name_en,
    w.city,
    a.is_swedavia_airport
from airports_agg a
left join src_airport_wiki w
    on a.iata_code = w.iata_code