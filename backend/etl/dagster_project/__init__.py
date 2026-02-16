from dagster import Definitions
from .assets import inat_raw, inat_refined, interactions, load_dbs
from .jobs import etl_job
from .schedules import daily_schedule

defs = Definitions(
    assets=[inat_raw, inat_refined, interactions, load_dbs],
    jobs=[etl_job],
    schedules=[daily_schedule],
)
