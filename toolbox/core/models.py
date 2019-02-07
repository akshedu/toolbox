
import datetime
from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.
class Thumbnail(models.Model):
    default_url = models.TextField(null=True)
    medium_url = models.TextField(null=True)
    high_url = models.TextField(null=True)


class Description(models.Model):
    description = models.TextField(null=True)


class Resource(models.Model):
    title = models.CharField(max_length=255)
    description = models.ForeignKey(Description, on_delete=models.CASCADE, null=True)
    published_at = models.DateTimeField(null=True)
    thumbnail = models.ForeignKey(Thumbnail, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now_add=True)

    def compare(self, obj):
        excluded_keys = '_state', 'last_updated', 'published_at'
        return self._compare(self, obj, excluded_keys)

    def _compare(self, obj1, obj2, excluded_keys):
        d1, d2 = obj1.__dict__, obj2.__dict__
        diff = {}
        for k,v in d1.items():
            if k in excluded_keys:
                continue
            elif k == 'description_id':
                if obj1.description.description != obj2.description.description:
                    diff['description'] = {'old': d1.description.description, 'new': d2.description.description}
            elif k == 'thumbnail_id':
                if obj2.thumbnail.default_url != obj2.thumbnail.default_url:
                    diff['thumbnail'] = {'old': d1.thumbnail.default_url, 'new': d2.thumbnail.default_url}
            elif v != d2[k]:
                diff[k] = {'old': v, 'new': d2[k]}
        return diff

    class Meta:
        abstract = True


class Channel(Resource):
    channel = models.OneToOneField('scraper.TrackedChannel', on_delete=models.CASCADE, primary_key=True)
    country = models.CharField(max_length=3, null=True, blank=True)
    

class ChannelVideoMap(models.Model):
    channel = models.ForeignKey(Channel, to_field='channel_id', on_delete=models.CASCADE)
    video_id = models.CharField(max_length=11, db_index=True, primary_key=True)

    class Meta:
        unique_together = ('channel', 'video_id',)


class Video(Resource):
    video = models.OneToOneField(ChannelVideoMap, to_field='video_id', on_delete=models.CASCADE, primary_key=True)
    duration = models.IntegerField(null=True)
    keywords = ArrayField(models.CharField(max_length=255,null=True),null=True)


class ChannelStats(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    views = models.BigIntegerField(null=True)
    comments = models.BigIntegerField(null=True)
    subscribers = models.BigIntegerField(null=True)
    video_count = models.IntegerField(null=True)
    crawled_date = models.DateField(default=datetime.date.today)

    class Meta:
        unique_together = ('channel', 'crawled_date',)


class VideoStats(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    views = models.BigIntegerField(null=True)
    likes = models.BigIntegerField(null=True)
    dislikes = models.BigIntegerField(null=True)
    favorites = models.BigIntegerField(null=True)
    comments = models.BigIntegerField(null=True)
    crawled_date = models.DateField(default=datetime.date.today)

    class Meta:
        unique_together = ('video', 'crawled_date',)


class TopResource(models.Model):
    metric = models.CharField(max_length=25)
    date = models.DateField(default=datetime.date.today)
    frequency = models.CharField(max_length=25)
    incremental = models.BigIntegerField(null=True)

    class Meta:
        abstract = True


class TopVideos(TopResource):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)


class TopChannels(TopResource):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)



class ResourceHistory(models.Model):
    field = models.CharField(max_length=25)
    old_value = models.TextField()
    new_value = models.TextField()
    crawled_date = models.DateField(default=datetime.date.today)

    class Meta:
        abstract = True 


class VideoHistory(ResourceHistory):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)


class ChannelHistory(ResourceHistory):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
