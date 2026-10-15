{{ config(enabled=false) }}
with wiki_airlines as (
    select * from {{ source('swedavia', 'wiki_airlines') }}
)

select
    upper(trim(iata))        as iata_code,
    upper(trim(icao))        as icao_code,
    airline                  as airline_name,
    callsign                 as callsign,
    country_region           as country
from wiki_airlines
where iata is not null
qualify row_number() over (partition by upper(trim(iata)) order by airline) = 1