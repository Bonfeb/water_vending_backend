# orders/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from orders.models import *
from orders.serializers import *
from products.models import *
from core.permissions import *
from core.notifications import *


class OrderListCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        orders = Order.objects.filter(user=request.user).order_by('-created_at')

        serializer = OrderSerializer(orders, many=True)
        
        return Response(serializer.data)
    
    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        pricing = Pricing.objects.get(size=data['size'])
        unit_price = pricing.purchase_price if data['order_type'] == 'purchase' else pricing.refill_price
        total = unit_price * data['quantity']

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            order_type=data['order_type'],
            bottle_id=data.get('bottle_id'),
            size=data['size'],
            quantity=data['quantity'],
            total_amount=total,
            payment_phone=data['payment_phone'],
            delivery_address=data['delivery_address'],
            delivery_lat=data.get('delivery_lat'),
            delivery_lng=data.get('delivery_lng'),
            delivery_notes=data.get('delivery_notes', ''),
            status='pending'
        )

        return Response({
            'order': OrderSerializer(order).data,
            'message': 'Order created. Proceed to payment.'
        }, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def delete(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        if order.status not in ['pending', 'paid']:
            return Response({'error': 'Cannot cancel'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'cancelled'
        order.save()
        return Response({'message': 'Order cancelled'})


class AdminOrderListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        status_filter = request.query_params.get('status')
        orders = Order.objects.all()
        if status_filter:
            orders = orders.filter(status=status_filter)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class AssignRiderView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = AssignRiderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from users.models import User
        order = get_object_or_404(Order, pk=serializer.validated_data['order_id'])
        rider = get_object_or_404(User, pk=serializer.validated_data['rider_id'], is_rider=True)

        if order.status != 'paid':
            return Response({'error': 'Order must be paid first'}, status=status.HTTP_400_BAD_REQUEST)

        order.rider = rider
        order.status = 'assigned'
        order.save()

        notify_rider(rider, 'New Delivery', f'Assigned Order #{order.id}')
        notify_customer(order.user, 'Rider Assigned', f'Rider {rider.first_name} assigned to your order')

        return Response(OrderSerializer(order).data)


class RiderOrderListView(APIView):
    permission_classes = [IsRider]

    def get(self, request):
        orders = Order.objects.filter(rider=request.user, status__in=['assigned', 'picked', 'in_transit'])
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class RiderUpdateStatusView(APIView):
    permission_classes = [IsRider]

    def post(self, request):
        serializer = UpdateStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, pk=request.data.get('order_id'), rider=request.user)
        new_status = serializer.validated_data['status']

        valid = {
            'assigned': ['picked'],
            'picked': ['in_transit'],
            'in_transit': ['delivered']
        }

        if order.status not in valid or new_status not in valid.get(order.status, []):
            return Response({'error': 'Invalid transition'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        if new_status == 'picked':
            order.picked_at = timezone.now()
        elif new_status == 'delivered':
            order.delivered_at = timezone.now()
        order.save()

        notify_customer(order.user, 'Order Update', f'Order #{order.id} is now {new_status.replace("_", " ").title()}')

        return Response(OrderSerializer(order).data)


class CustomerOrderTrackingView(APIView):
    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        if not order.rider:
            return Response({'error': 'No rider assigned'}, status=status.HTTP_400_BAD_REQUEST)

        rider = order.rider
        return Response({
            'order_id': order.id,
            'status': order.status,
            'rider': {
                'id': rider.id,
                'name': f"{rider.first_name} {rider.last_name}",
                'phone': rider.phone_number,
                'lat': str(rider.location_lat) if rider.location_lat else None,
                'lng': str(rider.location_lng) if rider.location_lng else None,
                'updated_at': rider.location_updated_at
            }
        })