from django.urls import path
from riders.views import *
from django.urls import re_path
from riders.consumers import *


urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('riders/active/', GetActiveRidersView.as_view(), name='active-riders'),
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard'),
]

websocket_urlpatterns = [
    re_path(r'ws/location/$', LocationConsumer.as_asgi()),
    re_path(r'ws/track/(?P<order_id>\d+)/$', OrderTrackingConsumer.as_asgi()),
]