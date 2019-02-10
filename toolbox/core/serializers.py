
import datetime

from rest_framework import serializers
from django.core import serializers as django_serializers
from toolbox.core.models import Video, VideoStats, ChannelStats


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
        model = Video
        fields = '__all__'

    def to_representation(self, instance):
        obj = super().to_representation(instance)
        yesterday = str((datetime.datetime.today() - datetime.timedelta(days=1)).date())
        stats = ChannelStats.objects.filter(
                        channel=instance, crawled_date=yesterday)\
                        .values('channel_id','views','subscribers','video_count','crawled_date')[0]
        obj['stats'] = stats

        Video.objects.filter(
                        video__channel=instance)

        return obj




