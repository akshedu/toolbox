
import datetime

from rest_framework import serializers
from django.core import serializers as django_serializers
from toolbox.core.models import Video, Description, VideoStats


class VideoSerializer(serializers.ModelSerializer):
    description = serializers.ReadOnlyField(source='description.description')
    thumbnail = serializers.ReadOnlyField(source='thumbnail.default_url')
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




