with di as (
    select * from (values
        ('D', 'Domestic'),
        ('S', 'Schengen'),
        ('I', 'International')
    ) as t(di_code, description)
)

select
    {{ dbt_utils.generate_surrogate_key(['di_code']) }}     as di_key,
    di_code,
    description
from di