from django.urls import path
from products.views import *

urlpatterns = [
    # Public
    path('products/pricing/', PublicPricingListView.as_view(), name='public-pricing'),
    path('products/sizes/', PublicBottleSizesView.as_view(), name='public-sizes'),
    path('products/calculate-total/', CalculateTotalView.as_view(), name='calculate-total'),
    path('inventory/', PublicInventoryView.as_view(), name='inventory'),
    
    # Staff management
    path('admin/bottles/', AdminBottleListCreateView.as_view(), name='admin-bottle-list-create'),
    path('admin/bottle/<int:pk>/', AdminBottleDetailView.as_view(), name='admin-bottle-detail'),
    path('admin/pricing/', AdminPricingListCreateView.as_view(), name='admin-pricing-list-create'),
    path('admin/pricing/<int:pk>/', AdminPricingDetailView.as_view(), name='admin-pricing-detail'),
]