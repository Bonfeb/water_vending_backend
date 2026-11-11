from django.urls import path
from products.views import *

urlpatterns = [
    # Public
    path('products/pricing/', PublicPricingListView.as_view(), name='public-pricing'),
    path('products/sizes/', PublicBottleSizesView.as_view(), name='public-sizes'),
    path('products/calculate-total/', CalculateTotalView.as_view(), name='calculate-total'),
    path('inventory/', PublicInventoryView.as_view(), name='inventory'),
    
    # Staff management
    path('bottles/', AdminBottleListCreateView.as_view(), name='admin-bottle-list-create'),
    path('bottle/<int:pk>/', AdminBottleDetailView.as_view(), name='admin-bottle-detail'),
    path('pricing/', AdminPricingListCreateView.as_view(), name='admin-pricing-list-create'),
    path('pricing/<int:pk>/', AdminPricingDetailView.as_view(), name='admin-pricing-detail'),
]