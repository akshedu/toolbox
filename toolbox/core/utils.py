
from toolbox.core.models import ChannelStats, VideoStats


def get_video_incremental_queryset(start_date, end_date, video_list=None):
    select_dict =   {
                        'inc_views': 'views - lag(views) over (partition by core_videostats.video_id order by crawled_date)',
                        'inc_likes': 'likes - lag(likes) over (partition by core_videostats.video_id order by crawled_date)',
                        'inc_comments': 'comments - lag(comments) over (partition by core_videostats.video_id order by crawled_date)'
                    }                    
    if not VideoStats.objects.filter(crawled_date=start_date).exists():
        return
    if not video_list:
        return VideoStats.objects.filter(crawled_date__in=[start_date, end_date]).extra(select=select_dict).values('video_id','inc_views','inc_likes','inc_comments')
    return VideoStats.objects.filter(crawled_date__in=[start_date, end_date], video_id__in=video_list).extra(select=select_dict).values('video_id','views','likes','dislikes','comments','inc_views','inc_likes','inc_comments','video__title','video__published_at','video__thumbnail_default_url')


def get_channel_incremental_queryset(start_date, end_date, channel_id=None):
    select_dict =   {
                        'inc_views': 'views - lag(views) over (partition by core_channelstats.channel_id order by crawled_date)',
                        'inc_subscribers': 'subscribers - lag(subscribers) over (partition by core_channelstats.channel_id order by crawled_date)'
                    }
    if not VideoStats.objects.filter(crawled_date=start_date).exists():
        return
    if not channel_id:
        return ChannelStats.objects.filter(crawled_date__in=[start_date, end_date]).extra(select=select_dict).values('channel_id','inc_views','inc_subscribers')
    return ChannelStats.objects.filter(crawled_date__range=(start_date, end_date), channel_id=channel_id).extra(select=select_dict).values('channel_id','inc_views','inc_subscribers','views','subscribers','video_count','crawled_date')


def update_resource_details(resource, data):
    for attr, value in data.items():
        setattr(resource, attr, value['new'])
    setattr(resource, 'last_updated', value)
    resource.save()