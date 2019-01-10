
import datetime
from django.db import models

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
	keywords = models.TextField(null=True)


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