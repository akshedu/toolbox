
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .utils import create_youtube_service

SCOPES = settings.YOUTUBE_SCOPES
SERVICE_ACCOUNT_FILE = settings.SERVICE_ACCOUNT_FILES[0]

# Create your models here.
class TrackedChannel(models.Model):
    channel_id = models.CharField(max_length=24, db_index=True, primary_key=True)
    added = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def clean(self):
        youtube = create_youtube_service(SCOPES, SERVICE_ACCOUNT_FILE)
        channel = youtube.channels().list(id=self.channel_id, part='snippet').execute()
        if channel['pageInfo']['totalResults'] != 1:
            raise ValidationError(_('The channel ID you have entered is not valid'))
