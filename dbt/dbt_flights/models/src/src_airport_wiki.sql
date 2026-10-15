{{ config(enabled=false) }}
with wiki_airports as (
    select * from {{ source('swedavia', 'wiki_airports') }}
)

select
    upper(trim(iata))    as iata_code,
    upper(trim(icao))    as icao_code,
    airport              as airport_name,
    location             as city
from wiki_airports
where iata is not null
qualify row_number() over (partition by upper(trim(iata)) order by airport) = 1