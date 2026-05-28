from rest_framework import serializers
from products.models import *
from users.serializers import *


class BottleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bottle
        fields = ['id', 'size', 'bottle_code', 'purchase_date', 'is_active']
        read_only_fields = ['bottle_code', 'purchase_date']


class PricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pricing
        fields = ['id', 'size', 'purchase_price', 'refill_price']