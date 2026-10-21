with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('" ~ var('dim_date_start') ~ "' as date)",
        end_date="dateadd(year, 2, current_date)"
    ) }}
)

select
    to_number(to_char(date_day, 'YYYYMMDD'))   as date_key,
    date_day::date                             as full_date,
    year(date_day)                             as year,
    quarter(date_day)                          as quarter,
    month(date_day)                            as month,
    weekiso(date_day)                          as week,
    dayofweekiso(date_day)                     as day_of_week,
    decode(dayofweekiso(date_day),
        1, 'Monday', 2, 'Tuesday', 3, 'Wednesday', 4, 'Thursday',
        5, 'Friday', 6, 'Saturday', 7, 'Sunday')  as weekday_name,
    dayofweekiso(date_day) in (6, 7)           as is_weekend
from spine