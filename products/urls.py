from django.urls import path
from products.views import *

urlpatterns = [
    path('bottles/', BottleListCreateView.as_view(), name='bottles'),
    path('bottles/<int:pk>/', BottleDetailView.as_view(), name='bottle-detail'),
    path('pricing/', PricingListView.as_view(), name='pricing'),
    path('pricing/calculate/', CalculateTotalView.as_view(), name='calculate'),
]