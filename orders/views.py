from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import AnonRateThrottle
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from orders.models import Order
from orders.serializers import *
from products.models import *
from core.permissions import IsStaffMember
from core.utils import standardize_phone_number
from users.models import User


class GuestAccessThrottle(AnonRateThrottle):
    """Limits phone-number guessing by unauthenticated users."""
    scope = 'guest_access'


def is_staff_user(user):
    return user.is_authenticated and user.groups.filter(name='staff').exists()


class OrderListCreateView(APIView):
    # Guests may create orders; listing is guarded inside get()
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to view your orders'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        orders = (
            Order.objects.filter(user=request.user)
            .select_related('user')
            .order_by('-created_at')
        )
        return Response(OrderSerializer(orders, many=True).data)

    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            pricing = Pricing.objects.get(size=data['size'])
        except Pricing.DoesNotExist:
            return Response(
                {'error': f'No pricing found for {data["size"]}L size'},
                status=status.HTTP_400_BAD_REQUEST
            )

        unit_price = (
            pricing.purchase_price if data['order_type'] == 'purchase'
            else pricing.refill_price
        )
        total = unit_price * data['quantity']

        # Check and lock stock BEFORE creating the order
        bottles = []
        if data['order_type'] == 'purchase':
            bottles = list(
                Bottle.objects.select_for_update()
                .filter(size=data['size'], is_active=True)[:data['quantity']]
            )
            if len(bottles) < data['quantity']:
                return Response(
                    {'error': f'Not enough {data["size"]}L bottles in stock '
                              f'({len(bottles)} available).'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        user = request.user if request.user.is_authenticated else None

        order = Order.objects.create(
            user=user,
            guest_name=data.get('guest_name', '') if not user else '',
            guest_phone=data.get('guest_phone', '') if not user else '',
            order_type=data['order_type'],
            size=data['size'],
            quantity=data['quantity'],
            total_amount=total,
            payment_phone=data.get('payment_phone', ''),
            delivery_address=data['delivery_address'],
            delivery_notes=data.get('delivery_notes', ''),
            status='pending'
        )

        if bottles:
            Bottle.objects.filter(
                pk__in=[b.pk for b in bottles]
            ).update(is_active=False)

        return Response({
            'order': OrderSerializer(order).data,
            'message': 'Order created successfully. Proceed to payment.'
        }, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [permissions.AllowAny]   # access is checked in _authorize
    throttle_classes = [GuestAccessThrottle]      # only throttles unauthenticated requests

    @staticmethod
    def _guest_phone(request, data):
        for source in (data, request.query_params):
            if source:
                raw = source.get('guest_phone_verify') or source.get('phone')
                if raw:
                    return raw
        return None

    def _authorize(self, request, order, data=None):
        user = request.user
        if user.is_authenticated:
            return is_staff_user(user) or order.user_id == user.id

        # Guests can only access guest orders, verified by phone number
        if order.user_id is not None or not order.guest_phone:
            return False
        raw = self._guest_phone(request, data)
        if not raw:
            return False
        try:
            phone = standardize_phone_number(raw)
        except ValueError:
            return False
        return order.guest_phone == phone

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        if not self._authorize(request, order):
            return Response(
                {'error': 'Permission denied. Provide phone verification for guest orders.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(OrderSerializer(order).data)

    def put(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        if not self._authorize(request, order, data=request.data):
            return Response(
                {'error': 'Permission denied. Provide phone verification for guest orders.'},
                status=status.HTTP_403_FORBIDDEN
            )

        is_staff = is_staff_user(request.user)

        if order.status != 'pending' and not is_staff:
            return Response(
                {'error': 'Only pending orders can be updated.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        recalculate = False
        if 'size' in data and data['size'] != order.size:
            order.size = data['size']
            recalculate = True
        if 'quantity' in data and data['quantity'] != order.quantity:
            order.quantity = data['quantity']
            recalculate = True

        if recalculate:
            try:
                pricing = Pricing.objects.get(size=order.size)
                unit_price = (
                    pricing.purchase_price if order.order_type == 'purchase'
                    else pricing.refill_price
                )
                order.total_amount = unit_price * order.quantity
            except Pricing.DoesNotExist:
                pass

        # guest_phone is NOT editable here: it is the guest's proof of ownership
        editable = ['delivery_address', 'delivery_notes']
        if order.user_id is None:
            editable.append('guest_name')

        for field in editable:
            if field in data:
                setattr(order, field, data[field])

        order.save()

        return Response({
            'order': OrderSerializer(order).data,
            'message': 'Order updated successfully'
        })

    def delete(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        if not self._authorize(request, order, data=request.data):
            return Response(
                {'error': 'Permission denied. Provide phone verification for guest orders.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if order.status not in ['pending', 'paid']:
            return Response(
                {'error': 'Cannot cancel order in its current status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()
        return Response({'message': 'Order cancelled successfully'})


class GuestOrderLookupView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [GuestAccessThrottle]

    def post(self, request):
        serializer = GuestOrderLookupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            phone = standardize_phone_number(
                serializer.validated_data['phone_number']
            )
        except ValueError:
            return Response(
                {'error': 'Invalid phone number format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Guest orders ONLY. Registered users' orders require logging in.
        orders = Order.objects.filter(
            user__isnull=True, guest_phone=phone
        ).order_by('-created_at')

        if not orders.exists():
            return Response(
                {'error': 'No orders found for this phone number.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(OrderSerializer(orders, many=True).data)

class AdminOrderListView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        orders = Order.objects.all()

        status_filter = request.query_params.get('status')
        order_type = request.query_params.get('order_type')
        search = request.query_params.get('search')

        if status_filter:
            orders = orders.filter(status=status_filter)
        if order_type:
            orders = orders.filter(order_type=order_type)
        if search:
            orders = orders.filter(
                Q(user__phone_number__icontains=search)
                | Q(guest_phone__icontains=search)
                | Q(guest_name__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(mpesa_receipt__icontains=search)
                | Q(delivery_address__icontains=search)
            )

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class AdminOrderDetailView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = AdminOrderUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Handle user reassignment
        if 'user_id' in data:
            if data['user_id']:
                new_user = get_object_or_404(User, pk=data['user_id'])
                order.user = new_user
                order.guest_name = ''
                order.guest_phone = ''
            else:
                order.user = None

        # Handle bottle
        if 'bottle_id' in data:
            order.bottle_id = data['bottle_id']

        # Recalculate total if size/quantity changed and total_amount not explicitly set
        recalculate = False
        if 'size' in data and data['size'] != order.size:
            order.size = data['size']
            recalculate = True
        if 'quantity' in data and data['quantity'] != order.quantity:
            order.quantity = data['quantity']
            recalculate = True

        if recalculate and 'total_amount' not in data:
            try:
                pricing = Pricing.objects.get(size=order.size)
                unit_price = (
                    pricing.purchase_price if order.order_type == 'purchase'
                    else pricing.refill_price
                )
                order.total_amount = unit_price * order.quantity
            except Pricing.DoesNotExist:
                pass

        # Update simple fields
        for field in [
            'status', 'delivery_address', 'delivery_notes',
            'total_amount', 'mpesa_receipt', 'payment_phone',
            'guest_name', 'guest_phone'
        ]:
            if field in data:
                setattr(order, field, data[field])

        order.save()

        return Response({
            'order': OrderSerializer(order).data,
            'message': 'Order updated by staff'
        })

    def delete(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order.status = 'cancelled'
        order.save()
        return Response({'message': 'Order cancelled by staff'})