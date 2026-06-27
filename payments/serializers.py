from rest_framework import serializers
from payments.models import *

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class STKPushSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=20)


class STKPushResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    checkout_request_id = serializers.CharField(required=False, allow_blank=True)
    merchant_request_id = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField()