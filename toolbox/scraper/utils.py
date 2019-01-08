
from google.oauth2 import service_account
import googleapiclient.discovery

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
SERVICE_ACCOUNT_FILE = '/Users/akshanshgupta/Downloads/project-id-8462122450179553311-3dedd987ff35.json'

def create_youtube_service(SCOPES, SERVICE_ACCOUNT_FILE):
	credentials = service_account.Credentials.from_service_account_file(
		SERVICE_ACCOUNT_FILE, scopes=SCOPES)
	return googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)