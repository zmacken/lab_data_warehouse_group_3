with wiki_airlines as (
    select * from {{ source('swedavia', 'wiki_airlines') }}
)

-- LLM has provided the some of the regex. 
select
    case when regexp_like(upper(trim(iata)), '^[A-Z0-9]{2}$') then upper(trim(iata)) end   as iata_code,
    case when regexp_like(upper(trim(icao)), '^[A-Z0-9]{3}$') then upper(trim(icao)) end   as icao_code,
    trim(regexp_replace(airline, '\\[[^\\]]*\\]', ''))                                      as airline_name,
    trim(telephony_designator)                                                              as callsign,
    trim(regexp_replace(country_region, '\\[[^\\]]*\\]', ''))                               as country,
    coalesce(lower(comments) like '%defunct%' or lower(comments) like '%ceased%', false)    as is_defunct
from wiki_airlines
where airline is not null