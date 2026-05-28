from rest_framework import serializers


class STKPushSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15)


class STKPushResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    checkout_request_id = serializers.CharField(required=False, allow_blank=True)
    merchant_request_id = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField()