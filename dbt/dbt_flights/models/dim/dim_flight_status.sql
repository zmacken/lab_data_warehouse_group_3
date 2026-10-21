with src_flights as (select * from {{ ref('src_flights') }})

select
    {{ dbt_utils.generate_surrogate_key(['status_code']) }}     as status_key,
    status_code,
    max(trim(regexp_replace(status_text_sv, '[[:space:]]*[0-9]{1,2}:[0-9]{2}.*$', '')))  as text_sv,
    max(trim(regexp_replace(status_text_en, '[[:space:]]*[0-9]{1,2}:[0-9]{2}.*$', '')))  as text_en
from src_flights
group by status_code