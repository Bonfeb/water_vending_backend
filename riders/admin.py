from django.contrib import admin
from riders.models import *


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']


@admin.register(DashboardStat)
class DashboardStatAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_orders', 'total_revenue', 'delivered_orders']