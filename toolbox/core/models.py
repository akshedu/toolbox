from django.db import models

# Create your models here.
class Thumbnail(models.Model):
	default_url = models.TextField()
	medium_url = models.TextField()
	high_url = models.TextField()


class Description(models.Model):
	description = models.TextField()


class Resource(models.Model):
	title = models.CharField(max_length=255)
	description = models.ForeignKey(Description, on_delete=models.CASCADE)
	published_at = models.DateTimeField()
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
	duration = models.IntegerField()
	keywords = models.TextField()


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
	video = models.ForeignKey(Video, on_delete=models.CASCADE)
	views = models.BigIntegerField()
	likes = models.BigIntegerField()
	dislikes = models.BigIntegerField()
	favorites = models.BigIntegerField()
	comments = models.BigIntegerField()
	crawled_date = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('video', 'crawled_date',)