
from itertools import chain
import datetime

from toolbox.core.models import Video, VideoStats, ChannelVideoMap, Channel
from toolbox.core.models import TopVideos, TopChannels, ChannelStats
from toolbox.scraper.models import TrackedChannel
from toolbox.core.serializers import VideoSerializer, ChannelSerializer
from toolbox.core.utils import get_channel_top_incremental_videos, \
    get_channel_all_videos, get_channel_daily_stats, get_published_count_timerange, \
    get_published_bins_timerange, get_duration_statistics, get_tags_statistics

from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet, ViewSet
from rest_framework.response import Response
from django.utils import timezone
from toolbox.core import BadRequest

from django.db.models import Sum, F, Func

import pandas as pd

VIDEO_ALLOWED_METRICS = ['inc_views', 'inc_likes', 'inc_comments']
CHANNEL_ALLOWED_METRICS = ['inc_views', 'inc_subscribers']

TIMERANGE_DICT = {'daily': 1,
                  'weekly': 7,
                  'monthly': 30}


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


class ChannelViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    lookup_field = 'channel_id'


class VideoHistory(ViewSet):
    def list(self, request, timerange):
        video_id = request.query_params.get('id')
        check_input('video_id', video_id)
        timerange = int(timerange)
        start_date = str((datetime.datetime.today() -
                          datetime.timedelta(days=timerange+1)).date())
        data = VideoStats.objects.filter(
            video_id=video_id, crawled_date__gte=start_date).values('crawled_date', 'views')
        return Response(data)


class ChannelHistory(ViewSet):
    def list(self, request, timerange):
        channel_id = request.query_params.get('id')
        check_input('channel_id', channel_id)
        timerange = int(timerange)
        start_date = str((datetime.datetime.today() -
                          datetime.timedelta(days=timerange+1)).date())
        data = ChannelStats.objects.filter(channel_id=channel_id, crawled_date__gte=start_date).values(
            'crawled_date', 'views', 'subscribers')
        return Response(data)


def validate_inputs(resource, request):
    metric = request.query_params.get('metric')
    check_input('metric', metric)
    end_date = request.query_params.get('endDate')
    check_input('endDate', end_date)
    validate_date(end_date)

    if resource == 'Video':
        if metric not in VIDEO_ALLOWED_METRICS:
            raise BadRequest('Invalid metric')

    if resource == 'Channel':
        if metric not in CHANNEL_ALLOWED_METRICS:
            raise BadRequest('Invalid metric')

    return metric, end_date


def get_top_videos_df(request, timerange):
    metric, end_date = validate_inputs('Video', request)
    top_videos_queryset = TopVideos.objects.filter(
        frequency=timerange, date=end_date, metric=metric)
    if not top_videos_queryset.exists():
        return None
    top_video_ids = list(
        top_videos_queryset.values_list('video_id', flat=True))
    top_videos_incremental = top_videos_queryset.values(
        'video_id', 'video__title', 'incremental', 'metric', 'video__video__channel__title')
    top_video_stats = VideoStats.objects.filter(video_id__in=top_video_ids, crawled_date=end_date).values(
        'video_id', 'views', 'likes', 'dislikes', 'comments')
    top_videos_incremental_df = pd.DataFrame(list(top_videos_incremental))
    top_videos_stats_df = pd.DataFrame(list(top_video_stats))
    top_videos = pd.merge(top_videos_incremental_df,
                          top_videos_stats_df, on='video_id')
    top_videos = top_videos.replace({pd.np.nan: None})
    return top_videos


class TopVideoViewSet(ViewSet):
    def list(self, request, timerange):
        top_videos = get_top_videos_df(request, timerange)
        if top_videos is None:
            return Response({'message': 'Very likely scrapers failed hence data is not available. Try with another endDate',
                             'status': 'failed'})
        result = {}
        result['status'] = 'success'
        result['data'] = top_videos.to_dict(orient='records')
        return Response(result)


class TopChannelViewSet(ViewSet):
    def list(self, request, timerange):
        metric, end_date = validate_inputs('Channel', request)
        top_channels_queryset = TopChannels.objects.filter(
            frequency=timerange, date=end_date, metric=metric)
        if not top_channels_queryset.exists():
            return Response({'message': 'Very likely scrapers failed hence data is not available. Try with another endDate',
                             'status': 'failed'})
        top_channel_ids = list(
            top_channels_queryset.values_list('channel_id', flat=True))
        top_channels_incremental = top_channels_queryset.values(
            'channel_id', 'channel__title', 'incremental', 'metric')
        top_channels_stats = ChannelStats.objects.filter(
            channel_id__in=top_channel_ids, crawled_date=end_date).values('channel_id', 'views', 'subscribers')
        top_channels_incremental_df = pd.DataFrame(
            list(top_channels_incremental))
        top_channels_stats_df = pd.DataFrame(list(top_channels_stats))
        top_channels = pd.merge(
            top_channels_incremental_df, top_channels_stats_df, on='channel_id')
        result = {}
        result['status'] = 'success'
        result['data'] = top_channels.to_dict(orient='records')
        return Response(result)


class OverviewSet(ViewSet):
    def list(self, request):
        data = {}
        data['total_tracked_channels'] = TrackedChannel.objects.filter(
            active=True).count()
        data['total_tracked_videos'] = Video.objects.count()
        data['total_views'] = VideoStats.objects.filter(
            crawled_date=timezone.now()).aggregate(Sum('views'))['views__sum']
        data['total_subscribers'] = ChannelStats.objects.filter(
            crawled_date=timezone.now()).aggregate(Sum('subscribers'))['subscribers__sum']
        return Response(data)


class TopKeywordsViewSet(ViewSet):
    def list(self, request, timerange):
        top_videos = get_top_videos_df(request, timerange)
        if top_videos is None:
            return Response({'message': 'Very likely scrapers failed hence data is not available. Try with another endDate',
                             'status': 'failed'})
        top_video_ids = top_videos.video_id.tolist()
        video_keywords_df = pd.DataFrame(list(Video.objects.filter(video_id__in=top_video_ids).annotate(
            keyword=Func(F('keywords'), function='unnest')).values('video_id', 'keyword')))
        top_keywords_incremental_df = pd.merge(
            top_videos, video_keywords_df, on='video_id')
        top_keywords_incremental_df = top_keywords_incremental_df.groupby('keyword')['incremental']\
            .sum().reset_index().sort_values('incremental', ascending=False).head(50)
        top_keywords_video_ids = video_keywords_df[video_keywords_df.keyword.isin(
            top_keywords_incremental_df.keyword)].video_id.unique()

        result = {}
        result['top_keywords'] = top_keywords_incremental_df.to_dict(
            orient='records')
        result['top_videos'] = top_videos[top_videos.video_id.isin(
            top_keywords_video_ids)].to_dict(orient='records')
        return Response(result)


class StatisticsPublishedViewSet(ViewSet):
    def list(self, request, timerange):
        metric, end_date = validate_inputs('Statistics', request)
        timerange = int(timerange)
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        start_date = end_date - datetime.timedelta(days=timerange)
        channel_id = request.query_params.get('channel_id')
        video_published_df = get_published_bins_timerange(start_date, end_date, channel_id)
        return Response(video_published_df)


class StatisticsDurationViewSet(ViewSet):
    def list(self, request, timerange):
        metric, end_date = validate_inputs('Statistics', request)
        timerange = int(timerange)
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        start_date = end_date - datetime.timedelta(days=timerange)
        channel_id = request.query_params.get('channel_id')
        video_published_df = get_duration_statistics(start_date, end_date, channel_id)
        return Response(video_published_df)


class StatisticsVideoViewSet(ViewSet):
    def list(self, request, timerange):
        metric, end_date = validate_inputs('Statistics', request)
        video_stats = VideoStats.objects.filter(crawled_date=end_date).values(
            'video_id', 'views', 'likes', 'dislikes', 'comments', 'video__title')
        video_stats_df = pd.DataFrame(list(video_stats))
        video_stats_df = video_stats_df.dropna(subset=['views'])
        video_stats_df['views_bins'] = pd.cut(video_stats_df['views'], bins=[
                                              0, 10000, 50000, 100000, 500000, 1000000, 10000000, 10000000000], include_lowest=True).astype(str)
        video_views_df = video_stats_df.groupby(['views_bins'])['video_id'].count(
        ).reset_index().rename(columns={'video_id': 'video_count'})
        result = {}
        result['views_distribution'] = video_views_df.to_dict()
        result['top_videos'] = video_stats_df.replace({pd.np.nan: None}).sort_values(
            ['views'], ascending=False).head(100).to_dict(orient='records')
        return Response(result)


class StatisticsKeywordsViewSet(ViewSet):
    def list(self, request, timerange):
        metric, end_date = validate_inputs('Statistics', request)
        timerange = int(timerange)
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        start_date = end_date - datetime.timedelta(days=timerange)
        channel_id = request.query_params.get('channel_id')
        video_keywords_df = get_tags_statistics(start_date, end_date, channel_id)
        return Response(video_keywords_df)


class StatisticsUploadsViewSet(ViewSet):
    def list(self, request, timerange):
        metric, end_date = validate_inputs('Statistics', request)
        timerange = int(timerange)
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        start_date = end_date - datetime.timedelta(days=timerange)
        channel_id = request.query_params.get('channel_id')
        video_published_df = get_published_count_timerange(start_date, end_date, timerange, channel_id)
        channel_subscribers_df = pd.DataFrame(list(ChannelStats.objects.filter(channel_id__in=video_published_df.channel_id.unique(
        ).tolist(), crawled_date=end_date).values('channel_id', 'views', 'video_count', 'subscribers')))
        video_channel_df = pd.merge(
            video_published_df, channel_subscribers_df, on='channel_id')
        results = {}
        results['top_channels'] = video_channel_df.sort_values(
            'uploads_per_week', ascending=False).to_dict(orient='records')
        video_channel_df['subscribers_bins'] = pd.cut(video_channel_df['subscribers'], bins=[
                                                      0, 50000, 100000, 500000, 1000000, 3000000, 50000000]).astype(str)
        video_channel_df['uploads_per_week_bins'] = pd.cut(video_channel_df['uploads_per_week'], bins=[
                                                           0, 2, 4, 6, 8, 10, 1000], include_lowest=True).astype(str)
        results['subscribers_bins_average'] = video_channel_df.groupby('subscribers_bins')['uploads_per_week'].mean(
        ).reset_index().rename(columns={'uploads_per_week': 'average_uploads'}).to_dict(orient='records')
        results['subscribers_uploads_distribution'] = video_channel_df.groupby(['subscribers_bins', 'uploads_per_week_bins'])[
            'channel_id'].count().reset_index().rename(columns={'channel_id': 'channel_count'}).to_dict(orient='records')
        return Response(results)


class ChannelTopVideosViewSet(ViewSet):
    def list(self, request, timerange):
        metric, end_date = validate_inputs('Channel', request)
        timerange = TIMERANGE_DICT[timerange]
        channel_id = request.query_params.get('channel_id')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        start_date = end_date - datetime.timedelta(days=timerange)
        df = get_channel_top_incremental_videos(channel_id, start_date, end_date)
        return Response(df.to_dict(orient='records'))


class ChannelAllVideosViewSet(ViewSet):
    def list(self, request):
        metric, end_date = validate_inputs('Channel', request)
        channel_id = request.query_params.get('channel_id')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        df = get_channel_all_videos(channel_id, end_date)
        return Response(df.to_dict(orient='records'))


class ChannelDailyStatsViewSet(ViewSet):
    def list(self, request, timerange):
        metric, end_date = validate_inputs('Channel', request)
        timerange = int(timerange)
        channel_id = request.query_params.get('channel_id')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        start_date = end_date - datetime.timedelta(days=timerange)
        df = get_channel_daily_stats(channel_id, start_date, end_date)
        return Response(df.to_dict(orient='records'))
