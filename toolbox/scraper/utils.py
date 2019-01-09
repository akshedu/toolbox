
from google.oauth2 import service_account
import googleapiclient.discovery


def create_youtube_service(SCOPES, SERVICE_ACCOUNT_FILE):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)


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

    try:
        uploads_list_id = channel_query_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        playlistItem_query = youtube.playlistItems().list(
            playlistId=uploads_list_id,
            part="snippet",
            maxResults=50
            )
        while playlistItem_query:
            playlistItem_query_response = playlistItem_query.execute()
            for item in playlistItem_query_response.get("items",[]):
                temp_channel_id.append(item['snippet']['channelId'])
                temp_video_id.append(item['snippet']['resourceId']['videoId'])
            playlistItem_query = youtube.playlistItems().list_next(playlistItem_query,playlistItem_query_response)
    except:
        print('Data not found for channel id {}'.format(channel_id))


def get_channel_details(youtube, channel_ids):
  channel_query_response = youtube.channels().list(
    part='snippet,statistics',
    id=channel_ids
    ).execute()

  for item in channel_query_response.get("items", []):
    try:
        channelID.append(item['id'])
    except:
        channelID.append('')
    try:
      channel_title.append(item['snippet']['title'])
    except:
      channel_title.append('')
    try:
        views.append(item['statistics']['viewCount'])
    except:
        views.append('')
    try:
        comments.append(item['statistics']['commentCount'])
    except KeyError:
        comments.append('')
    try:
      subs.append(item['statistics']['subscriberCount'])
    except:
      subs.append('')
    try:
      videos.append(item['statistics']['videoCount'])
    except:
      videos.append('')