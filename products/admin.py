from django.contrib import admin
from products.models import *


@admin.register(Bottle)
class BottleAdmin(admin.ModelAdmin):
    list_display = ['size', 'purchase_date', 'is_active']
    list_filter = ['size', 'is_active']
    actions = ['mark_as_sold']
    #search_fields = ['user__phone_number', 'user__first_name']

    @admin.action(description='Mark selected as sold/damaged')
    def mark_as_sold(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Pricing)
class PricingAdmin(admin.ModelAdmin):
    list_display = ['size', 'purchase_price', 'refill_price']