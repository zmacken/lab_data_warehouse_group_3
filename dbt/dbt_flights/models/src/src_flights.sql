with unioned as (
    select * from {{ ref('src_arrivals') }}
    union all by name
    select * from {{ ref('src_departures') }}
)

select
    *,
    convert_timezone('UTC', 'Europe/Stockholm', scheduled_utc)::date as scheduled_local_date
from unioned