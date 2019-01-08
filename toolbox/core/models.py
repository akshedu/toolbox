from django.db import models

# Create your models here.
class Channel(models.Model):
	channel = models.OneToOneField('scraper.TrackedChannel', on_delete=models.CASCADE, primary_key=True)
	title = models.CharField()
	description = models.TextField()
	published_at = models.DateTimeField()
	country = models.CharField(null=True, blank=True)
	last_updated = models.DateTimeField(auto_now_add=True)


class ChannelVideoMap(models.Model):
	channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
	video_id = models.CharField(max_length=11, db_index=True, unique=True)

	class Meta:
		unique_together = ('channel', 'video',)


class Video(models.Model):
	video = models.ForeignKey(ChannelVideoMap, to_field='video_id', on_delete=models.CASCADE, unique=True)
	title = models.CharField()
	duration = models.IntegerField()
	keywords = models.TextField()
	published_date = models.DateTimeField()
	last_updated = models.DateTimeField(auto_now_add=True)


class ChannelStats(models.Model):
	channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
	views = models.BigIntegerField()
	comments = models.BigIntegerField()
	subscribers = models.BigIntegerField()
	video_count = models.IntegerField()
	crawled_date = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('channel', 'crawled_date',)


class VideoStats(models.Model):
	video = models.ForeignKey(Video, to_field='video_id', on_delete=models.CASCADE)
	views = models.BigIntegerField()
	likes = models.BigIntegerField()
	comments = models.BigIntegerField()
	crawled_date = models.DateTimeField()

	class Meta:
		unique_together = ('video', 'crawled_date',)