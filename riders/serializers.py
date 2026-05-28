from rest_framework import serializers
from riders.models import *


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'created_at']


class RiderLocationSerializer(serializers.Serializer):
    rider_id = serializers.IntegerField()
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6)
    updated_at = serializers.DateTimeField()


class ActiveRiderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    phone = serializers.CharField()
    lat = serializers.CharField()
    lng = serializers.CharField()
    updated_at = serializers.DateTimeField()
    current_order = serializers.DictField(required=False, allow_null=True)