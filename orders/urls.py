from django.urls import path
from orders.views import*

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='orders'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/track/<int:order_id>/', CustomerOrderTrackingView.as_view(), name='track-order'),
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-orders'),
    path('admin/assign-rider/', AssignRiderView.as_view(), name='assign-rider'),
    path('rider/orders/', RiderOrderListView.as_view(), name='rider-orders'),
    path('rider/update-status/', RiderUpdateStatusView.as_view(), name='update-status'),
]