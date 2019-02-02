
from itertools import chain
import datetime

from toolbox.core.models import Video, VideoStats
from toolbox.core.models import TopVideos, TopChannels, ChannelStats
from toolbox.scraper.models import TrackedChannel
from toolbox.core.serializers import VideoSerializer

from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet, ViewSet
from rest_framework.response import Response
from django.utils import timezone
from toolbox.core import BadRequest

from django.db.models import Sum, F, Func

import pandas as pd

VIDEO_ALLOWED_METRICS = ['inc_views', 'inc_likes', 'inc_comments']
CHANNEL_ALLOWED_METRICS = ['inc_views', 'inc_subscribers']
ALLOWED_FREQUENCY = ['daily', 'weekly', 'monthly']


def check_input(arg, value):
    if value is None or value == '':
        raise BadRequest('Missing parameter: %s' % arg)


def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise BadRequest('Bad date: %s' % date_text)


class VideoViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    lookup_field = 'video_id'


def validate_inputs(resource, request):
    timerange = request.query_params.get('timerange')
    check_input('timerange', timerange)
    metric = request.query_params.get('metric')
    check_input('metric', metric)
    end_date = request.query_params.get('endDate')
    check_input('endDate', end_date)
    validate_date(end_date)

    if timerange not in ALLOWED_FREQUENCY:
        raise BadRequest('Invalid timerange')

    if resource == 'Video':
        if metric not in VIDEO_ALLOWED_METRICS:
            raise BadRequest('Invalid metric')

    if resource == 'Channel':
        if metric not in CHANNEL_ALLOWED_METRICS:
            raise BadRequest('Invalid metric')

    return timerange, metric, end_date


def get_top_videos_df(request):
        timerange, metric, end_date = validate_inputs('Video', request)
        top_videos_queryset = TopVideos.objects.filter(frequency=timerange, date=end_date, metric=metric)
        if not top_videos_queryset.exists():
            return None
        top_video_ids = list(top_videos_queryset.values_list('video_id', flat=True))
        top_videos_incremental = top_videos_queryset.values('video_id','video__title','incremental','metric')
        top_video_stats = VideoStats.objects.filter(video_id__in=top_video_ids, crawled_date=end_date).values('video_id','views','likes','dislikes','comments')
        top_videos_incremental_df = pd.DataFrame(list(top_videos_incremental))
        top_videos_stats_df = pd.DataFrame(list(top_video_stats))
        top_videos = pd.merge(top_videos_incremental_df, top_videos_stats_df, on='video_id')
        top_videos = top_videos.replace({pd.np.nan:None})
        return top_videos


class TopVideoViewSet(ViewSet):
    def list(self, request):
        top_videos = get_top_videos_df(request)
        if top_videos is None:
            return Response({'message':'Very likely scrapers failed hence data is not available. Try with another endDate',
                             'status':'failed'})
        print(top_videos)
        result = {}
        result['status'] = 'success'
        result['data'] = top_videos.to_dict(orient='records')
        return Response(result)


class TopChannelViewSet(ViewSet):
    def list(self, request):
        timerange, metric, end_date = validate_inputs('Channel', request)
        top_channels_queryset = TopChannels.objects.filter(frequency=timerange, date=end_date, metric=metric)
        if not top_channels_queryset.exists():
            return Response({'message':'Very likely scrapers failed hence data is not available. Try with another endDate',
                             'status':'failed'})
        top_channel_ids = list(top_channels_queryset.values_list('channel_id', flat=True))
        top_channels_incremental = top_channels_queryset.values('channel_id','channel__title','incremental','metric')
        top_channels_stats = ChannelStats.objects.filter(channel_id__in=top_channel_ids, crawled_date=end_date).values('channel_id','views','subscribers')
        top_channels_incremental_df = pd.DataFrame(list(top_channels_incremental))
        top_channels_stats_df = pd.DataFrame(list(top_channels_stats))
        top_channels = pd.merge(top_channels_incremental_df, top_channels_stats_df, on='channel_id')
        result = {}
        result['status'] = 'success'
        result['data'] = top_channels.to_dict(orient='records')

        return Response(result)


class OverviewSet(ViewSet):
    def list(self, request):
        data = {}
        data['total_tracked_channels'] = TrackedChannel.objects.filter(active=True).count()
        data['total_tracked_videos'] = Video.objects.count()
        data['total_views'] = VideoStats.objects.filter(crawled_date=timezone.now()).aggregate(Sum('views'))['views__sum']
        data['total_subscribers'] = ChannelStats.objects.filter(crawled_date=timezone.now()).aggregate(Sum('subscribers'))['subscribers__sum']
        return Response(data)


class TopKeywordsViewSet(ViewSet):
    def list(self, request):
        top_videos = get_top_videos_df(request)
        if top_videos is None:
            return Response({'message':'Very likely scrapers failed hence data is not available. Try with another endDate',
                             'status':'failed'})
        top_video_ids = top_videos.video_id.tolist()
        video_keywords_df = pd.DataFrame(list(Video.objects.filter(video_id__in=top_video_ids).annotate(keyword=Func(F('keywords'), function='unnest')).values('video_id', 'keyword')))
        top_keywords_incremental_df = pd.merge(top_videos, video_keywords_df, on='video_id')
        top_keywords_incremental_df = top_keywords_incremental_df.groupby('keyword')['incremental']\
                                        .sum().reset_index().sort_values('incremental',ascending=False).head(50)
        top_keywords_video_ids = video_keywords_df[video_keywords_df.keyword.isin(top_keywords_incremental_df.keyword)].video_id.unique()

        result = {}
        result['top_keywords'] = top_keywords_incremental_df.to_dict(orient='records')
        result['top_videos'] = top_videos[top_videos.video_id.isin(top_keywords_video_ids)].to_dict(orient='records')
        return Response(result)
