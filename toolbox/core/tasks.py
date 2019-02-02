
from __future__ import absolute_import
import isodate
import pandas as pd

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .utils import get_video_incremental_queryset, get_channel_incremental_queryset

from toolbox.core.models import ChannelStats, VideoStats, TopVideos, TopChannels


@shared_task
def create_top_videos():
    for timerange in settings.TIMERANGE_DICT.keys():
        start_date = timezone.now() - timezone.timedelta(days=settings.TIMERANGE_DICT[timerange])
        end_date = timezone.now() - timezone.timedelta(days=1)
        video_incremental = get_video_incremental_queryset(start_date, end_date)
        if video_incremental is None:
            continue
        video_incremental_df = pd.DataFrame(list(video_incremental))
        video_incremental_df = pd.melt(video_incremental_df, id_vars=['video_id'], var_name='metric', value_name='incremental')
        video_incremental_df = video_incremental_df.dropna()
        video_incremental_df = video_incremental_df.sort_values(['metric','incremental'],ascending=[False,False]).groupby('metric').head(settings.TOP_RESOURCE_LIMIT)
        to_create = []
        for index, row in video_incremental_df.iterrows():
            to_create.append(TopVideos(video_id=row['video_id'],
                                       metric=row['metric'],
                                       date=end_date,
                                       frequency=timerange,
                                       incremental=row['incremental']))
        TopVideos.objects.bulk_create(to_create)


@shared_task
def create_top_channels():
    for timerange in settings.TIMERANGE_DICT.keys():
        start_date = timezone.now() - timezone.timedelta(days=settings.TIMERANGE_DICT[timerange])
        end_date = timezone.now() - timezone.timedelta(days=1)
        channel_incremental = get_channel_incremental_queryset(start_date, end_date)
        if channel_incremental is None:
            continue
        channel_incremental_df = pd.DataFrame(list(channel_incremental))
        channel_incremental_df = pd.melt(channel_incremental_df, id_vars=['channel_id'], var_name='metric', value_name='incremental')
        channel_incremental_df = channel_incremental_df.dropna()
        channel_incremental_df = channel_incremental_df.sort_values(['metric','incremental'],ascending=[False,False]).groupby('metric').head(settings.TOP_RESOURCE_LIMIT)
        to_create = []
        for index, row in channel_incremental_df.iterrows():
            to_create.append(TopChannels(channel_id=row['channel_id'],
                                       metric=row['metric'],
                                       date=end_date,
                                       frequency=timerange,
                                       incremental=row['incremental']))
        TopChannels.objects.bulk_create(to_create)


            