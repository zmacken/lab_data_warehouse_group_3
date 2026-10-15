select * from {{ ref('src_arrivals') }}
union all by name
select * from {{ ref('src_departures') }}