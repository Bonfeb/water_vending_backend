from django.contrib import admin
from payments.models import *


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'phone_number', 'amount', 'status', 'mpesa_receipt', 'created_at']
    list_filter = ['status']


@admin.register(MPesaTransactionLog)
class MPesaTransactionLogAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'created_at']