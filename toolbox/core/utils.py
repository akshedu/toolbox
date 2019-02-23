
from toolbox.core.models import ChannelStats, VideoStats, ChannelVideoMap, Video
import pandas as pd


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
    if not ChannelStats.objects.filter(crawled_date=start_date).exists():
        return
    if not channel_id:
        return ChannelStats.objects.filter(crawled_date__in=[start_date, end_date]).extra(select=select_dict).values('channel_id','inc_views','inc_subscribers')
    return ChannelStats.objects.filter(crawled_date__range=(start_date, end_date), channel_id=channel_id).extra(select=select_dict).values('channel_id','inc_views','inc_subscribers','views','subscribers','video_count','crawled_date')


def update_resource_details(resource, data):
    for attr, value in data.items():
        setattr(resource, attr, value['new'])
    resource.save()


def get_channel_top_incremental_videos(channel_id, start_date, end_date):
    video_list = list(ChannelVideoMap.objects.filter(
        channel_id=channel_id).values_list('video_id', flat=True))
    video_incremental = get_video_incremental_queryset(
        start_date, end_date, video_list)
    video_incremental_df = pd.DataFrame(list(video_incremental))
    video_incremental_df = video_incremental_df.sort_values(
        'inc_views', ascending=False).head(50)
    return video_incremental_df


def get_channel_all_videos(channel_id, end_date):
    video_list = list(ChannelVideoMap.objects.filter(
        channel_id=channel_id).values_list('video_id', flat=True))
    video_df = VideoStats.objects.filter(crawled_date=end_date, video_id__in=video_list).values(
        'video_id', 'views', 'likes', 'dislikes', 'comments', 'video__title', 'video__published_at', 'video__thumbnail_default_url')
    video_df = pd.DataFrame(list(video_df))
    video_df = video_df.replace({pd.np.nan: None})
    return video_df


def get_channel_daily_stats(channel_id, start_date, end_date):
    channel_incremental = get_channel_incremental_queryset(
        start_date, end_date, channel_id)
    print(channel_incremental)
    channel_incremental_df = pd.DataFrame(list(channel_incremental))
    channel_incremental_df = channel_incremental_df[channel_incremental_df.crawled_date != start_date.date()]
    channel_incremental_df['crawled_date'] = pd.to_datetime(
        channel_incremental_df.crawled_date)
    channel_incremental_df['day'] = channel_incremental_df.crawled_date.dt.day_name(
    )
    channel_incremental_df = channel_incremental_df.dropna(subset=['inc_views'])
    return channel_incremental_df


def get_published_count_timerange(start_date, end_date, timerange, channel_id=None):
    if channel_id:
        video_published_df = pd.DataFrame(list(ChannelVideoMap.objects.filter(
            video__published_at__range=(start_date, end_date),channel_id=channel_id).values('channel_id', 'video_id')))
    else:
        video_published_df = pd.DataFrame(list(ChannelVideoMap.objects.filter(
            video__published_at__range=(start_date, end_date)).values('channel_id', 'video_id')))
    video_published_df = video_published_df.groupby('channel_id').count(
    ).reset_index().rename(columns={'video_id': 'published_count'})
    if timerange == 7:
        video_published_df['uploads_per_week'] = video_published_df['published_count']
    if timerange == 30:
        video_published_df['uploads_per_week'] = video_published_df['published_count'] / 4
    if timerange == 90:
        video_published_df['uploads_per_week'] = video_published_df['published_count'] / 12
    return video_published_df


def get_published_bins_timerange(start_date, end_date, channel_id=None):
    if channel_id:
        video_published_df = pd.DataFrame(list(Video.objects.filter(
            published_at__range=(start_date, end_date), video__channel_id=channel_id).values('video_id', 'published_at')))  
    else:      
        video_published_df = pd.DataFrame(list(Video.objects.filter(
            published_at__range=(start_date, end_date)).values('video_id', 'published_at')))
    video_published_df['weekday'] = video_published_df.published_at.dt.weekday_name
    video_published_df['hour'] = video_published_df.published_at.dt.hour
    video_published_df['hour_bins'] = pd.cut(video_published_df['hour'], bins=[
                                             0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24], include_lowest=True).astype(str)
    video_views = pd.DataFrame(list(VideoStats.objects.filter(
        video_id__in=video_published_df.video_id.tolist(), crawled_date=end_date).values('video_id', 'views')))
    video_published_df = pd.merge(
        video_published_df, video_views, on='video_id')
    video_published_df = video_published_df.groupby(['weekday', 'hour_bins'])[
        'views'].sum().reset_index()
    return video_published_df


def get_duration_statistics(start_date, end_date, channel_id=None):
    if channel_id:
        video_published_df = pd.DataFrame(list(Video.objects.filter(
            published_at__range=(start_date, end_date), video__channel_id=channel_id).values('video_id', 'duration')))
    else:
        video_published_df = pd.DataFrame(list(Video.objects.filter(
            published_at__range=(start_date, end_date)).values('video_id', 'duration')))
    video_published_df['duration_bins'] = pd.cut(
        video_published_df['duration'], bins=list(range(0, 7200, 10))).astype(str)
    video_published_df = video_published_df.groupby(['duration_bins'])[
        'video_id'].count().reset_index().rename(columns={'video_id': 'video_count'})
    return video_published_df


def get_tags_statistics(start_date, end_date, channel_id=None):
    if channel_id:
        video_keywords_df = pd.DataFrame(list(Video.objects.filter(published_at__range=(
            start_date, end_date), video__channel_id=channel_id).extra(select={'length': 'cardinality(keywords)'}).values('video_id', 'length')))
    else:       
        video_keywords_df = pd.DataFrame(list(Video.objects.filter(published_at__range=(
            start_date, end_date)).extra(select={'length': 'cardinality(keywords)'}).values('video_id', 'length')))
    video_keywords_df = video_keywords_df.groupby(['length'])['video_id'].count(
    ).reset_index().rename(columns={'video_id': 'video_count'})
    return video_keywords_df
