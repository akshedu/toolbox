
from itertools import chain

from toolbox.core.models import Video
from toolbox.core.models import VideoStats, TopVideos
from toolbox.core.serializers import VideoSerializer

from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet, ViewSet
from rest_framework.response import Response
from django.utils import timezone
from toolbox.core import BadRequest

from django.db.models.functions import Lag
from django.db.models.expressions import RawSQL


def check_input(arg, value):
    if value is None or value == '':
        raise BadRequest('Missing parameter: %s' % arg)


class VideoViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    lookup_field = 'video_id'


class TopVideoViewSet(ViewSet):
	def list(self, request):
		timerange = request.query_params.get('timerange')
		check_input('timerange', timerange)
		metric = request.query_params.get('metric')
		check_input('metric', metric)

		if timerange not in ['daily', 'weekly', 'monthly']:
			raise BadRequest('timerange must be one of daily, weekly or monthly')

		if metric not in ['views', 'likes', 'comments', 'hotness']:
			raise BadRequest('metric must be one of views, likes, comments or hotness')




