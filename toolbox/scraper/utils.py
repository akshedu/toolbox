
from google.oauth2 import service_account
import googleapiclient.discovery

from toolbox.core.models import ChannelStats, VideoStats


def create_youtube_service(SCOPES, SERVICE_ACCOUNT_FILE):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return googleapiclient.discovery.build('youtube', 'v3', credentials=credentials, cache_discovery=False)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def chunkify(list, n):
  """Yield total of n splits for the given list (not in order)"""
  return [list[i::n] for i in range(n)]


def get_channel_videos(youtube, channel_id):
    temp_video_id = []
    temp_channel_id = []
    # Call the Analytics API to retrieve a report. For a list of available
    # reports, see:
    # https://developers.google.com/youtube/analytics/v1/channel_reports
    channel_query_response = youtube.channels().list(
        part='contentDetails',
        id=channel_id,
        fields='items/contentDetails'
    ).execute()
    # Get the videos using the uploads playlist
    try:
        uploads_list_id = channel_query_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        playlistItem_query = youtube.playlistItems().list(
            playlistId=uploads_list_id,
            part="snippet",
            maxResults=50
            )
        while playlistItem_query:
            playlistItem_query_response = playlistItem_query.execute()
            yield playlistItem_query_response
            playlistItem_query = youtube.playlistItems().list_next(playlistItem_query,playlistItem_query_response)
    except:
        print('Data not found for channel id {}'.format(channel_id))


def get_channel_list(youtube, channel_ids, part):
    channel_ids = ','.join(str(v) for v in channel_ids)
    return youtube.channels().list(
        part=part,
        id=channel_ids
        ).execute()


def get_video_list(youtube, video_ids, part):
    video_ids = ','.join(str(v) for v in video_ids)
    return youtube.videos().list(
        part=part,
        id=video_ids
        ).execute()


def get_video_incremental_queryset(start_date, end_date):
    return VideoStats.objects.filter(crawled_date__in=[start_date, end_date]).extra(select={
                    'inc_views': 'views - lag(views) over (partition by video_id order by crawled_date)',
                    'inc_likes': 'likes - lag(likes) over (partition by video_id order by crawled_date)',
                    'inc_comments': 'comments - lag(comments) over (partition by video_id order by crawled_date)'
                }).values('video_id','inc_views','inc_likes','inc_comments')


def get_channel_incremental_queryset(start_date, end_date)
    return ChannelStats.objects.filter(crawled_date__in=[start_date, end_date]).extra(select={
                    'inc_views': 'views - lag(views) over (partition by channel_id order by crawled_date)',
                    'inc_subscribers': 'subscribers - lag(subscribers) over (partition by channel_id order by crawled_date)'
                }).values('video_id','inc_views','inc_subscribers')
