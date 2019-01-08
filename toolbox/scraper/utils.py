
from google.oauth2 import service_account
import googleapiclient.discovery

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
SERVICE_ACCOUNT_FILE = '/Users/akshanshgupta/Downloads/project-id-8462122450179553311-3dedd987ff35.json'

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
        print 'Data not found for channel id {}'.format(channel_id)