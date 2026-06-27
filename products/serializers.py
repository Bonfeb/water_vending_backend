from rest_framework import serializers
from products.models import *
from users.serializers import *

class BottleSerializer(serializers.ModelSerializer):
    size_display = serializers.CharField(source='get_size_display', read_only=True)

    class Meta:
        model = Bottle
        fields = [
            'id', 'size', 'size_display', 'purchase_date', 'is_active'
        ]
        read_only_fields = ['purchase_date']

class BottleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bottle
        fields = ['size', 'is_active']

class PricingSerializer(serializers.ModelSerializer):
    size_display = serializers.CharField(source='get_size_display', read_only=True)

    class Meta:
        model = Pricing
        fields = ['id', 'size', 'size_display', 'purchase_price', 'refill_price']