
from toolbox.core.models import ChannelStats, VideoStats


def get_video_incremental_queryset(start_date, end_date):
    if not VideoStats.objects.filter(crawled_date=start_date).exists():
        return
    return VideoStats.objects.filter(crawled_date__in=[start_date, end_date]).extra(select={
                    'inc_views': 'views - lag(views) over (partition by video_id order by crawled_date)',
                    'inc_likes': 'likes - lag(likes) over (partition by video_id order by crawled_date)',
                    'inc_comments': 'comments - lag(comments) over (partition by video_id order by crawled_date)'
                }).values('video_id','inc_views','inc_likes','inc_comments')


def get_channel_incremental_queryset(start_date, end_date):
    if not VideoStats.objects.filter(crawled_date=start_date).exists():
        return
    return ChannelStats.objects.filter(crawled_date__in=[start_date, end_date]).extra(select={
                    'inc_views': 'views - lag(views) over (partition by channel_id order by crawled_date)',
                    'inc_subscribers': 'subscribers - lag(subscribers) over (partition by channel_id order by crawled_date)'
                }).values('channel_id','inc_views','inc_subscribers')


def update_resource_details(resource, data):
    for attr, value in data.items():
        setattr(resource, attr, value['new'])
    setattr(resource, 'last_updated', value)
    resource.save()