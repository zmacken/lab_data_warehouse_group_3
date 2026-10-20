{{config(materialized="view")}}

WITH fct AS (
    SELECT * FROM {{ref("fct_flight_movement")}}
),
dim_airport AS (
    SELECT * FROM {{ref("dim_airport")}}
),
dim_airline AS (
    SELECT * FROM {{ref("dim_airline")}}
),
dim_date AS (
    SELECT * FROM {{ref("dim_date")}}
)

SELECT
    fct.flight_id,
    fct.direction,
    fct.scheduled_utc,
    fct.actual_utc,
    fct.delay_minutes,
    fct.is_delayed,

    dim_airline.name as airline_name,
    apt_local.city as airport_city,
    apt_local.name_sv as airport_name_sv,
    apt_other.city as other_airport_city,
    apt_other.name_sv as other_airport_name_sv,

    dim_date.date_key,
    dim_date.full_date,
    dim_date.year,
    dim_date.month,
    dim_date.day_of_week,
    dim_date.is_weekend

    FROM fct

    LEFT JOIN dim_airline
        ON fct.airline_key = dim_airline.airline_key
    
    LEFT JOIN dim_airport as apt_local
        ON fct.airport_key = apt_local.airport_key

    LEFT JOIN dim_airport as apt_other
        ON fct.other_airport_key = apt_other.airport_key

    LEFT JOIN dim_date
        ON fct.scheduled_date_key = dim_date.date_key