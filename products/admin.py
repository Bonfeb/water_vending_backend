from django.contrib import admin
from .models import Bottle, Pricing


@admin.register(Bottle)
class BottleAdmin(admin.ModelAdmin):
    list_display = ['user', 'size', 'purchase_date', 'is_active']
    list_filter = ['size', 'is_active']


@admin.register(Pricing)
class PricingAdmin(admin.ModelAdmin):
    list_display = ['size', 'purchase_price', 'refill_price']