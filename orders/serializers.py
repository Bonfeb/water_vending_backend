from rest_framework import serializers
from orders.models import *
from users.serializers import *
from products.serializers import *


class OrderSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    rider_details = UserSerializer(source='rider', read_only=True)
    bottle_details = BottleSerializer(source='bottle', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'user_details', 'order_type', 'bottle', 'bottle_details',
                  'size', 'quantity', 'status', 'rider', 'rider_details', 'total_amount',
                  'mpesa_receipt', 'payment_phone', 'delivery_address',
                  'delivery_lat', 'delivery_lng', 'delivery_notes',
                  'created_at', 'updated_at', 'picked_at', 'delivered_at']
        read_only_fields = ['status', 'mpesa_receipt', 'rider']


class OrderCreateSerializer(serializers.Serializer):
    order_type = serializers.ChoiceField(choices=Order.ORDER_TYPE_CHOICES)
    size = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    bottle_id = serializers.IntegerField(required=False, allow_null=True)
    payment_phone = serializers.CharField(max_length=15)
    delivery_address = serializers.CharField()
    delivery_lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    delivery_lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    delivery_notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
    
        request = self.context.get('request')
        user = request.user

        if data['order_type'] == 'refill' and not data.get('bottle_id'):
            raise serializers.ValidationError(
                "Bottle ID required for refill"
            )
        
        if data['order_type'] == 'refill' and not user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication required for refill orders"
            )

        if data['order_type'] == 'refill' and data.get('bottle_id'):

            try:

                if user.is_authenticated:
                    bottle = Bottle.objects.get(
                        id=data['bottle_id'],
                        user=user
                    )
                else:
                    bottle = Bottle.objects.get(
                        id=data['bottle_id']
                    )

                if bottle.size != data['size']:
                    raise serializers.ValidationError(
                        "Bottle size mismatch"
                    )

            except Bottle.DoesNotExist:
                raise serializers.ValidationError(
                    "Invalid bottle"
                )

        return data


class AssignRiderSerializer(serializers.Serializer):
    rider_id = serializers.IntegerField()
    order_id = serializers.IntegerField()


class UpdateStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        ('picked', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ])