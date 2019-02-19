
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views import defaults as default_views

from rest_framework.routers import DefaultRouter

from toolbox.core.views import VideoViewSet, \
        TopVideoViewSet, TopChannelViewSet, \
        OverviewSet, TopKeywordsViewSet, StatisticsPublishedViewSet, \
        StatisticsDurationViewSet, StatisticsVideoViewSet, \
        StatisticsKeywordsViewSet, VideoHistory, StatisticsUploadsViewSet, \
        ChannelTopVideosViewSet, ChannelViewSet, ChannelAllVideosViewSet, \
        ChannelDailyStatsViewSet

timerange_string = "(?P<timerange>daily|weekly|monthly)"
timerange_string_days = "(?P<timerange>7|30|90)"

router = DefaultRouter()
router.register(r'videos', VideoViewSet)
router.register(r'channels', ChannelViewSet)
router.register(r'top/videos/{}'.format(timerange_string), TopVideoViewSet, base_name='top_videos')
router.register(r'top/channels/{}'.format(timerange_string), TopChannelViewSet, base_name='top_channels')
router.register(r'overview', OverviewSet, base_name='overview')
router.register(r'top/keywords/{}'.format(timerange_string), TopKeywordsViewSet, base_name='top_keywords')
router.register(r'statistics/published/{}'.format(timerange_string_days), StatisticsPublishedViewSet, base_name='stats_published')
router.register(r'statistics/duration/{}'.format(timerange_string_days), StatisticsDurationViewSet, base_name='stats_duration')
router.register(r'statistics/videoview/{}'.format(timerange_string_days), StatisticsVideoViewSet, base_name='stats_videoview')
router.register(r'statistics/tags/{}'.format(timerange_string_days), StatisticsKeywordsViewSet, base_name='stats_tags')
router.register(r'history/{}'.format(timerange_string_days), VideoHistory, base_name='views_history')
router.register(r'statistics/uploads/{}'.format(timerange_string_days), StatisticsUploadsViewSet, base_name='stats_uploads')
router.register(r'channel/topvideos/{}'.format(timerange_string), ChannelTopVideosViewSet, base_name='channel_top_videos')
router.register(r'channel/allvideos', ChannelAllVideosViewSet, base_name='channel_all_videos')
router.register(r'channel/dailystats/{}'.format(timerange_string_days), ChannelDailyStatsViewSet, base_name='channel_daily_stats')

urlpatterns = [
    path('api/', include(router.urls)),
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "users/",
        include("toolbox.users.urls", namespace="users"),
    ),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
