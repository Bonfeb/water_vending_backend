from django.contrib import admin
from orders.models import *


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer_name', 'customer_phone', 'order_type',
        'size', 'status', 'total_amount', 'delivery_address', 'created_at'
    ]
    list_filter = ['status', 'order_type', 'size']
    search_fields = [
        'user__phone_number', 'guest_phone', 'guest_name', 'mpesa_receipt'
    ]