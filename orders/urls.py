from django.urls import path
from orders.views import *

urlpatterns = [
    # Customer / Guest
    path('orders/',OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/guest-lookup/', GuestOrderLookupView.as_view(), name='guest-order-lookup'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    
    # Staff
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<int:pk>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
]