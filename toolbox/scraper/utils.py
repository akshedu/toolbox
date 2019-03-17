
from google.oauth2 import service_account
import googleapiclient.discovery
from django.db import connection
from googleapiclient.errors import HttpError
from backoff import on_exception, expo as exponential

YT_Exceptions = ['userRateLimitExceeded', 'quotaExceeded',
                 'internalServerError', 'backendError']


def get_videos_to_scrape(today):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT video_id FROM 
                        (SELECT a.video_id AS video_id, last_scraped 
                        FROM core_channelvideomap a LEFT JOIN core_video b 
                        ON a.video_id = b.video_id) sub 
                        WHERE last_scraped != %s or last_scraped is NULL""", [today])
        video_list = cursor.fetchall()
    return [i[0] for i in video_list]


def create_youtube_service(SCOPES, SERVICE_ACCOUNT_FILE):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return googleapiclient.discovery.build('youtube', 'v3',
                                           credentials=credentials, cache_discovery=False)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def chunkify(list, n):
    """Yield total of n splits for the given list (not in order)"""
    return [list[i::n] for i in range(n)]


def get_channel_videos(youtube, channel_id):
    channel_query_response = get_channel_query(youtube, channel_id)
    # Get the videos using the uploads playlist
    if channel_query_response and channel_query_response['items']:
        try:
            uploads_list_id = channel_query_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            playlistItem_query = get_playlist_items_query(youtube, uploads_list_id)
            while playlistItem_query:
                playlistItem_query_response = get_playlist_items(playlistItem_query)
                if not playlistItem_query_response:
                    print("ERROR channel id {} uploads id {}".format(channel_id, uploads_list_id))
                yield playlistItem_query_response
                playlistItem_query = get_playlist_items_next(youtube, playlistItem_query, playlistItem_query_response)
        except Exception as e:
            print('Data not found for channel id {} due to {}'.format(channel_id, e))
    else:
        print("Empty channel query response for channel_id {}".format(channel_id))


class YTBackendException(Exception):
    pass


@on_exception(exponential, YTBackendException, max_tries=3)
def get_channel_list(youtube, channel_ids, part):
    channel_ids = ','.join(str(v) for v in channel_ids)
    try:
        return youtube.channels().list(part=part, id=channel_ids).execute()
    except HttpError as e:
        if e.resp.reason in YT_Exceptions:
            raise YTBackendException()
        else:
            print('Unknown HttpError {}'.format(e))
            return {}
    except Exception as e:
       print('Unknown exception {}'.format(e))
       return {}


@on_exception(exponential, YTBackendException, max_tries=3)
def get_video_list(youtube, video_ids, part):
    video_ids = ','.join(str(v) for v in video_ids)
    try:
        return youtube.videos().list(part=part, id=video_ids).execute()
    except HttpError as e:
        if e.resp.reason in YT_Exceptions:
            raise YTBackendException()
        else:
            print('Unknown HttpError {}'.format(e))
            return {}
    except Exception as e:
        print('Unknown exception {}'.format(e))
        return {}


def get_playlist_items_query(youtube, uploads_list_id):
    return youtube.playlistItems().list(
        playlistId=uploads_list_id,
        part="snippet",
        maxResults=50
    )


@on_exception(exponential, YTBackendException, max_tries=3)
def get_playlist_items(playlist_items_query):
    try:
        return playlist_items_query.execute()
    except HttpError as e:
        if e.resp.reason in YT_Exceptions:
            raise YTBackendException()


@on_exception(exponential, YTBackendException, max_tries=3)
def get_playlist_items_next(youtube, playlistItem_query, playlistItem_query_response):
    try:
        return youtube.playlistItems().list_next(
            playlistItem_query, playlistItem_query_response)
    except HttpError as e:
        if e.resp.reason in YT_Exceptions:
            raise YTBackendException()


@on_exception(exponential, YTBackendException, max_tries=3)
def get_channel_query(youtube, channel_id):
    try:
        return youtube.channels().list(
            part='contentDetails',
            id=channel_id,
            fields='items/contentDetails'
        ).execute()
    except HttpError as e:
        if e.resp.reason in YT_Exceptions:
            raise YTBackendException()
        else:
            print('Unknown HttpError {}'.format(e))
            return {}
    except Exception as e:
       print('Unknown exception {}'.format(e))
       return {}
