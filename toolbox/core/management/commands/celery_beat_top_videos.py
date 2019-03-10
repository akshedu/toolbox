
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='23',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',)
        PeriodicTask.objects.create(
            crontab=schedule,
            name='Top Videos',
            task='toolbox.core.create_top_videos',
        )

        PeriodicTask.objects.create(
            crontab=schedule,
            name='Top Channels',
            task='toolbox.core.create_top_channels',
        )
