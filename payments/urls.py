from django.urls import path
from payments.views import *

urlpatterns = [
    path('stk-push/', InitiateSTKPushView.as_view(), name='stk-push'),
    path('callback/', MPesaCallbackView.as_view(), name='mpesa-callback'),
    path('status/<int:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
]