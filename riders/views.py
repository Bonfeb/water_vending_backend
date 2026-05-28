from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from riders.models import *
from riders.serializers import *
from core.permissions import *
from users.models import *
from orders.models import *


class NotificationListView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All marked as read'})


class GetActiveRidersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        thirty_mins_ago = timezone.now() - timezone.timedelta(minutes=30)
        riders = User.objects.filter(
            is_rider=True,
            location_updated_at__gte=thirty_mins_ago
        )

        data = []
        for rider in riders:
            current_order = Order.objects.filter(
                rider=rider,
                status__in=['assigned', 'picked', 'in_transit']
            ).first()

            data.append({
                'id': rider.id,
                'name': f"{rider.first_name} {rider.last_name}",
                'phone': rider.phone_number,
                'lat': str(rider.location_lat) if rider.location_lat else None,
                'lng': str(rider.location_lng) if rider.location_lng else None,
                'updated_at': rider.location_updated_at,
                'current_order': {
                    'id': current_order.id,
                    'status': current_order.status,
                    'delivery_address': current_order.delivery_address
                } if current_order else None
            })

        return Response(data)


class DashboardStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.now().date()

        stats = {
            'total_orders_today': Order.objects.filter(created_at__date=today).count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
            'paid_orders': Order.objects.filter(status='paid').count(),
            'assigned_orders': Order.objects.filter(status='assigned').count(),
            'in_transit_orders': Order.objects.filter(status='in_transit').count(),
            'delivered_today': Order.objects.filter(delivered_at__date=today).count(),
            'total_revenue_today': Order.objects.filter(
                created_at__date=today,
                status__in=['paid', 'assigned', 'picked', 'in_transit', 'delivered']
            ).aggregate(total=models.Sum('total_amount'))['total'] or 0,
            'active_riders': User.objects.filter(is_rider=True).count(),
            'online_riders': User.objects.filter(
                is_rider=True,
                location_updated_at__gte=timezone.now() - timezone.timedelta(minutes=30)
            ).count(),
            'total_customers': User.objects.filter(is_rider=False, is_admin=False).count()
        }
        return Response(stats)