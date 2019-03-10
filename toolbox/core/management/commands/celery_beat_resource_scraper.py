
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            schedule_channel, created = IntervalSchedule.objects.get_or_create(
                                    every=4,
                                    period=IntervalSchedule.HOURS,
                                )
        except IntegrityError as e:
            pass

        try:
            schedule_video, created = IntervalSchedule.objects.get_or_create(
                                    every=6,
                                    period=IntervalSchedule.HOURS,
                                )
        except IntegrityError as e:
            pass

        try:
            PeriodicTask.objects.create(
                interval=schedule_channel,                  
                name='Scrape Channels',          
                task='toolbox.scraper.scrape_youtube_channels',  
            )
        except IntegrityError as e:
            pass

        try:
            PeriodicTask.objects.create(
                interval=schedule_video,                  
                name='Scrape Videos',          
                task='toolbox.scraper.scrape_youtube_videos',  
            )
        except IntegrityError as e:
            pass


