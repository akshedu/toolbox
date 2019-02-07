
from __future__ import absolute_import
import isodate

from celery import shared_task
from django.conf import settings
from toolbox.scraper.utils import create_youtube_service, \
    chunkify, chunks, get_channel_list, \
    get_video_list, get_channel_videos
from toolbox.core.utils import update_resource_details

from toolbox.scraper.models import TrackedChannel
from toolbox.core.models import Channel, ChannelStats, Video, \
    VideoStats, ChannelVideoMap, \
    VideoHistory, ChannelHistory

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

    for video_chunks in chunks(video_list, settings.YOUTUBE_RESOURCE_LIST_LIMIT):
        video_details_task(youtube_service, video_chunks, VIDEO_DETAILS_PART)

    for video_chunks in chunks(video_list, settings.YOUTUBE_RESOURCE_LIST_LIMIT):
        video_stats_task(youtube_service, video_chunks, RESOURCE_STATISTICS_PART)


@shared_task
def scrape_youtube_channel_chunks(channel_list, service_account_file):
    try:
        youtube_service = create_youtube_service(settings.YOUTUBE_SCOPES, service_account_file)
    except Exception as e:
        print("Cannot create youtube services due to {}.".format(e))

    for channel_chunks in chunks(channel_list, settings.YOUTUBE_RESOURCE_LIST_LIMIT):
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
        channel_id = item.get('id', None)
        channel = Channel(
                    channel_id=channel_id,
                    description=tem.get('snippet',{}).get('description', None),
                    title=item.get('snippet',{}).get('title', None),
                    published_at=item.get('snippet',{}).get('publishedAt', None),
                    thumbnail_default_url=default_url=item.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url', None),
                    thumbnail_medium_url=item.get('snippet', {}).get('thumbnails', {}).get('medium', {}).get('url', None),
                    thumbnail_high_url=item.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url', None),
                    country=item.get('snippet',{}).get('country', None))

        if not Channel.objects.filter(channel_id=channel_id).exists():
            channels_to_create.append(channel)
        else:     
            old = Channel.objects.get(channel_id=channel_id)
            diff = old.compare(channel)
            if diff:
                for field, d in diff.items():
                    ChannelHistory.objects.create(
                        channel_id=channel_id,
                        field=field,
                        old_value=d['old'],
                        new_value=d['new'])
                update_resource_details(old, diff)
    Channel.objects.bulk_create(channels_to_create)


#@shared_task
def video_details_task(youtube_service, video_list, part):
    video_query_response = get_video_list(youtube_service, video_list, part)
    videos_to_create = []
    for item in video_query_response.get('items', []):
        video_id = item.get('id', None)
        video = Video(
                    video_id=video_id,
                    description=item.get('snippet',{}).get('description', None),
                    title=item.get('snippet',{}).get('title', None),
                    published_at=item.get('snippet',{}).get('publishedAt', None),
                    thumbnail_default_url=item.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url', None),
                    thumbnail_medium_url=item.get('snippet', {}).get('thumbnails', {}).get('medium', {}).get('url', None),
                    thumbnail_high_url=item.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url', None),
                    duration=isodate.parse_duration(item.get('contentDetails', {}).get('duration', None)).total_seconds(),
                    keywords=item.get('snippet', {}).get('tags', None))

        if not Video.objects.filter(video_id=video_id).exists():
            videos_to_create.append(video)
        else:
            old = Video.objects.get(video_id=video_id)
            diff = old.compare(video)
            print(diff)
            if diff:
                for field, d in diff.items():
                    VideoHistory.objects.create(
                        video_id=video_id,
                        field=field,
                        old_value=d['old'],
                        new_value=d['new'])
                update_resource_details(old, diff)
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
