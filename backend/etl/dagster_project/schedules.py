from dagster import ScheduleDefinition
from .jobs import etl_job
daily_schedule = ScheduleDefinition(job=etl_job, cron_schedule="0 2 * * *")
