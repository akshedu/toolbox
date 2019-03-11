
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour='23',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',)
        except IntegrityError as e:
            pass

        try:
            PeriodicTask.objects.create(
                crontab=schedule,
                name='Top Videos',
                task='toolbox.core.tasks.create_top_videos',
            )
        except IntegrityError as e:
            pass

        try:
            PeriodicTask.objects.create(
                crontab=schedule,
                name='Top Channels',
                task='toolbox.core.tasks.create_top_channels',
            )
        except IntegrityError as e:
            pass
