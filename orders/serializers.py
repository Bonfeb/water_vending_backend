from rest_framework import serializers
from orders.models import Order
from users.serializers import UserSerializer
from products.serializers import BottleSerializer
from core.utils import standardize_phone_number


class OrderSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    bottle_details = BottleSerializer(source='bottle', read_only=True)
    customer_name = serializers.ReadOnlyField()
    customer_phone = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_details', 'guest_name', 'guest_phone',
            'customer_name', 'customer_phone',
            'order_type', 'bottle', 'bottle_details',
            'size', 'quantity', 'status',
            'total_amount', 'mpesa_receipt', 'payment_phone',
            'delivery_address', 'delivery_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'mpesa_receipt']


class OrderCreateSerializer(serializers.Serializer):
    """Handles order creation for both authenticated and guest users."""
    order_type = serializers.ChoiceField(choices=Order.ORDER_TYPE_CHOICES)
    size = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    payment_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    delivery_address = serializers.CharField()
    delivery_notes = serializers.CharField(required=False, allow_blank=True, default='')
    # Guest-only fields
    guest_name = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    guest_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request.user.is_authenticated else None

        # Guest users must provide name and phone
        if not user:
            if not data.get('guest_name', '').strip():
                raise serializers.ValidationError({
                    'guest_name': 'Name is required for guest orders.'
                })
            if not data.get('guest_phone', '').strip():
                raise serializers.ValidationError({
                    'guest_phone': 'Phone number is required for guest orders.'
                })
            try:
                data['guest_phone'] = standardize_phone_number(data['guest_phone'])
            except ValueError:
                raise serializers.ValidationError({
                    'guest_phone': 'Invalid phone number. Use 0712345678 or +254712345678'
                })

        if data['order_type'] == 'purchase':
            in_stock = Bottle.objects.filter(size=data['size'], is_active=True).count()
            if in_stock < data['quantity']:
                raise serializers.ValidationError({'quantity': f"Only {in_stock} bottles of {data['size']}L in stock available"})
        # Validate bottle_id if provided (optional for all types)
        if data.get('bottle_id'):
            try:
                from products.models import Bottle
                if user:
                    bottle = Bottle.objects.get(id=data['bottle_id'], user=user)
                else:
                    bottle = Bottle.objects.get(id=data['bottle_id'])

                if bottle.size != data['size']:
                    raise serializers.ValidationError({
                        'size': f'Bottle size mismatch. The bottle is {bottle.get_size_display()}.'
                    })
            except Exception:
                raise serializers.ValidationError({
                    'bottle_id': 'Invalid bottle selected.'
                })

        # Standardize payment_phone if provided
        if data.get('payment_phone'):
            try:
                data['payment_phone'] = standardize_phone_number(data['payment_phone'])
            except ValueError:
                raise serializers.ValidationError({
                    'payment_phone': 'Invalid payment phone number format.'
                })

        return data


class OrderUpdateSerializer(serializers.Serializer):
    """For customers to update their pending orders."""
    delivery_address = serializers.CharField(required=False)
    delivery_notes = serializers.CharField(required=False, allow_blank=True)
    size = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=1, required=False)
    guest_name = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    guest_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    # Phone verification for guest updates
    guest_phone_verify = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )


class GuestOrderLookupSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)


class AdminOrderUpdateSerializer(serializers.Serializer):
    """For staff to update any field on any order."""
    status = serializers.ChoiceField(
        choices=Order.STATUS_CHOICES, required=False
    )
    size = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=1, required=False)
    delivery_address = serializers.CharField(required=False)
    delivery_notes = serializers.CharField(required=False, allow_blank=True)
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    mpesa_receipt = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )
    payment_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    user_id = serializers.IntegerField(required=False, allow_null=True)
    guest_name = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    guest_phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    bottle_id = serializers.IntegerField(required=False, allow_null=True)