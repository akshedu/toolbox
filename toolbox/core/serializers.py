
import datetime
import pandas as pd

from rest_framework import serializers
from django.core import serializers as django_serializers
from toolbox.core.models import Video, VideoStats, ChannelStats, Channel, ChannelVideoMap
from toolbox.core.utils import get_published_count_timerange


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'

    def to_representation(self, instance):
        obj = super().to_representation(instance)
        yesterday = str((datetime.datetime.today() - datetime.timedelta(days=1)).date())
        stats = VideoStats.objects.filter(
                        video=instance, crawled_date=yesterday)\
                        .values('video_id','views','comments',
                                'likes','dislikes','crawled_date')[0]
        obj['stats'] = stats

        return obj


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = '__all__'

    def to_representation(self, instance):
        obj = super().to_representation(instance)
        yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
        timerange = 30
        start_date = yesterday - datetime.timedelta(days=timerange)
        yesterday = str(yesterday)
        stats = ChannelStats.objects.filter(
                        channel=instance, crawled_date=yesterday)\
                        .values('channel_id','views','subscribers','video_count','crawled_date')[0]
        obj['stats'] = stats
        obj['uploads_per_week'] = get_published_count_timerange(start_date, yesterday, timerange, channel_id=instance.channel_id).uploads_per_week.iloc[0]

        video_list = list(ChannelVideoMap.objects.filter(
            channel_id=instance.channel_id).values_list('video_id', flat=True))
        video_df = pd.DataFrame(list(VideoStats.objects.filter(crawled_date=yesterday, video_id__in=video_list).values(
            'video_id', 'views')))
        video_df['views_bins'] = pd.cut(video_df['views'], bins=[0, 100, 500, 1000, 5000, 10000, 
                                                                30000, 50000, 100000, 200000, 500000, 
                                                                1000000, 2000000, 3000000, 5000000, 
                                                                10000000,20000000, 30000000, 50000000,
                                                                10000000000], include_lowest=True).astype(str)
        views_distribution = video_df.groupby('views_bins')['video_id'].count().reset_index().rename(columns={'video_id': 'video_count'})
        obj['views_distribution'] = views_distribution.to_dict()
        return obj




