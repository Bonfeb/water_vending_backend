from django.contrib import admin
from orders.models import *


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'order_type', 'size', 'status', 'rider',
                    'total_amount', 'delivery_lat', 'delivery_lng', 'created_at']
    list_filter = ['status', 'order_type', 'size']
    search_fields = ['user__phone_number', 'mpesa_receipt']