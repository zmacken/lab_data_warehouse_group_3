with src_flights as (select * from {{ ref('src_flights') }}),

dates as (
    select distinct scheduled_utc::date as full_date
    from src_flights
    where scheduled_utc is not null
)

select
    to_number(to_char(full_date, 'YYYYMMDD'))   as date_key,
    full_date,
    year(full_date)                             as year,
    month(full_date)                            as month,
    dayofweekiso(full_date)                     as day_of_week,
    dayofweekiso(full_date) in (6, 7)           as is_weekend
from dates