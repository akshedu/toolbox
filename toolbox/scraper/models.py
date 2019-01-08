
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .utils import create_youtube_service

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
SERVICE_ACCOUNT_FILE = '/Users/akshanshgupta/Downloads/project-id-8462122450179553311-3dedd987ff35.json'

# Create your models here.
class TrackedChannel(models.Model):
    channel_id = models.CharField(max_length=24, db_index=True)
    added = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def clean(self):
        youtube = create_youtube_service(SCOPES, SERVICE_ACCOUNT_FILE)
        channel = youtube.channels().list(id=self.channel_id, part='snippet').execute()
        if channel['pageInfo']['totalResults'] != 1:
            raise ValidationError(_('The channel ID you have entered is not valid'))
