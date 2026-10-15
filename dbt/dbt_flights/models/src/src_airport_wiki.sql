with wiki_airports as (
    select * from {{ source('swedavia', 'wiki_airports') }}
),

-- LLM has provided the some of the regex. 
split_codes as (
    select
        upper(trim(regexp_replace(f.value::string, '\\[[^\\]]*\\]', '')))   as iata_code,
        trim(regexp_replace(w.location, '\\s*\\(.*\\)', ''))                 as city,
        trim(regexp_replace(w.airport, '\\[[^\\]]*\\]|\\*+', ''))            as airport_name
    from wiki_airports w,
        lateral flatten(input => split(w.iata_code, '/')) f
)

select iata_code, city, airport_name
from split_codes
where regexp_like(iata_code, '^[A-Z]{3}$')
qualify row_number() over (partition by iata_code order by airport_name) = 1