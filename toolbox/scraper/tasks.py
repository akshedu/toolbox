
from __future__ import absolute_import
import isodate

from celery import shared_task
from django.conf import settings
from toolbox.scraper.utils import create_youtube_service, chunkify, chunks, get_channel_list, get_video_list, get_channel_videos

from toolbox.scraper.models import TrackedChannel
from toolbox.core.models import Channel, ChannelStats, Thumbnail, Description, Video, VideoStats, ChannelVideoMap

VIDEO_DETAILS_PART = 'snippet,contentDetails'
CHANNEL_DETAILS_PART = 'snippet'
RESOURCE_STATISTICS_PART = 'statistics'

@shared_task
def scrape_youtube_channels():
    channel_list = list(TrackedChannel.objects.values_list('channel_id', flat=True))
    channel_chunks = list(chunkify(channel_list, settings.TRACKED_CHANNEL_SPLITS))
    for i in range(settings.TRACKED_CHANNEL_SPLITS):
        scrape_youtube_channel_chunks.delay(channel_chunks[i], settings.SERVICE_ACCOUNT_FILES[i])


@shared_task
def scrape_youtube_videos():
    video_list = list(ChannelVideoMap.objects.values_list('video_id', flat=True))
    video_chunks = list(chunkify(video_list, settings.TRACKED_CHANNEL_SPLITS))
    for i in range(settings.TRACKED_CHANNEL_SPLITS):
        scrape_youtube_video_chunks.delay(video_chunks[i], settings.SERVICE_ACCOUNT_FILES[i])


@shared_task
def scrape_youtube_video_chunks(video_list, service_account_file):
    try:
        youtube_service = create_youtube_service(settings.YOUTUBE_SCOPES, service_account_file)
    except Exception as e:
        print("Cannot create youtube services due to {}.".format(e))
    video_details_list = list(Video.objects.values_list('video_id', flat=True))
    video_details_missing = [video for video in video_list if video not in video_details_list]

    if not video_details_missing == []:
        for video_chunks in chunks(video_details_missing, settings.YOUTUBE_RESOURCE_LIST_LIMIT):
            video_details_task(youtube_service, video_chunks, VIDEO_DETAILS_PART)

    for video_chunks in chunks(video_list, settings.YOUTUBE_RESOURCE_LIST_LIMIT):
        video_stats_task(youtube_service, video_chunks, RESOURCE_STATISTICS_PART)


@shared_task
def scrape_youtube_channel_chunks(channel_list, service_account_file):
    try:
        youtube_service = create_youtube_service(settings.YOUTUBE_SCOPES, service_account_file)
    except Exception as e:
        print("Cannot create youtube services due to {}.".format(e))
    channel_details_list = list(Channel.objects.values_list('channel_id', flat=True))
    channel_details_missing = [channel for channel in channel_list if channel not in channel_details_list]

    if not channel_details_missing == []:
        for channel_chunks in chunks(channel_details_missing, settings.YOUTUBE_RESOURCE_LIST_LIMIT):
            channel_details_task(youtube_service, channel_chunks, CHANNEL_DETAILS_PART)

    for channel in channel_list:
        channel_videos_map_task(youtube_service, channel)

    for channel_chunks in chunks(channel_list, settings.YOUTUBE_RESOURCE_LIST_LIMIT):
        channel_stats_task(youtube_service, channel_chunks, RESOURCE_STATISTICS_PART)
        

#@shared_task
def channel_videos_map_task(youtube_service, channel_id):
    channel_video_map_to_create = []
    for response in get_channel_videos(youtube_service, channel_id):
        for item in response.get("items",[]):
            if not ChannelVideoMap.objects.filter(video_id=item.get('snippet', {}).get('resourceId', {}).get('videoId', None)).exists():
                channel_video_map_to_create.append(
                    ChannelVideoMap(
                        channel_id=item.get('snippet', {}).get('channelId', None),
                        video_id=item.get('snippet', {}).get('resourceId', {}).get('videoId', None)))

    ChannelVideoMap.objects.bulk_create(channel_video_map_to_create, batch_size=1000)


#@shared_task
def channel_stats_task(youtube_service, channel_list, part):
    channel_query_response = get_channel_list(youtube_service, channel_list, part)
    channel_stats_to_create = []
    for item in channel_query_response.get('items', []):
        channel_stats_to_create.append(
            ChannelStats(
                channel_id=item.get('id', None),
                views=item.get('statistics', {}).get('viewCount', None),
                comments=item.get('statistics', {}).get('commentCount', None),
                subscribers=item.get('statistics', {}).get('subscriberCount', None),
                video_count=item.get('statistics', {}).get('videoCount', None)))

    ChannelStats.objects.bulk_create(channel_stats_to_create)


#@shared_task
def channel_details_task(youtube_service, channel_list, part):
    channel_query_response = get_channel_list(youtube_service, channel_list, part)
    channels_to_create = []
    for item in channel_query_response.get('items', []):
        channels_to_create.append(
            Channel(
                channel_id=item.get('id', None),
                description=Description.objects.create(
                    description=item.get('snippet',{}).get('description', None)),
                title=item.get('snippet',{}).get('title', None),
                published_at=item.get('snippet',{}).get('publishedAt', None),
                thumbnail=Thumbnail.objects.create(
                    default_url=item.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url', None),
                    medium_url=item.get('snippet', {}).get('thumbnails', {}).get('medium', {}).get('url', None),
                    high_url=item.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url', None)),
                country=item.get('snippet',{}).get('country', None)))   

    Channel.objects.bulk_create(channels_to_create)


#@shared_task
def video_details_task(youtube_service, video_list, part):
    video_query_response = get_video_list(youtube_service, video_list, part)
    videos_to_create = []
    for item in video_query_response.get('items', []):
        videos_to_create.append(
            Video(
                video_id=item.get('id', None),
                description=Description.objects.create(
                    description=item.get('snippet',{}).get('description', None)),
                title=item.get('snippet',{}).get('title', None),
                published_at=item.get('snippet',{}).get('publishedAt', None),
                thumbnail=Thumbnail.objects.create(
                    default_url=item.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url', None),
                    medium_url=item.get('snippet', {}).get('thumbnails', {}).get('medium', {}).get('url', None),
                    high_url=item.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url', None)),
                duration=isodate.parse_duration(item.get('contentDetails', {}).get('duration', None)).total_seconds(),
                keywords=item.get('snippet', {}).get('tags', None)))

    Video.objects.bulk_create(videos_to_create)


#@shared_task
def video_stats_task(youtube_service, video_list, part):
    video_query_response = get_video_list(youtube_service, video_list, part)
    video_stats_to_create = []
    for item in video_query_response.get('items', []):
        video_stats_to_create.append(
            VideoStats(
                video_id=item.get('id', None),
                views=item.get('statistics', {}).get('viewCount', None),
                comments=item.get('statistics', {}).get('commentCount', None),
                likes=item.get('statistics', {}).get('likeCount', None),
                dislikes=item.get('statistics', {}).get('dislikeCount', None),
                favorites=item.get('statistics', {}).get('favoriteCount', None)))

    VideoStats.objects.bulk_create(video_stats_to_create)
