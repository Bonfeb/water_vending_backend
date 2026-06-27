from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from core.permissions import IsStaffMember
from django.utils import timezone
from datetime import timedelta
from users.models import *
from users.serializers import *
from products.models import *
from products.serializers import *
from orders.models import *
from orders.serializers import *
from payments.models import *
from payments.serializers import *

class RegisterView(APIView):
    """Register a new user → auto-add to 'customers' group."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        customers_group, _ = Group.objects.get_or_create(name='customers')
        user.groups.add(customers_group)

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """Login with phone_number + password."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = authenticate(username=phone_number, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is disabled'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful'
        })

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"message": "Invalid or expired refresh token"})

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')

        return Response({
            'user': UserSerializer(request.user, context={'request': request}).data,
            'orders': OrderSerializer(orders, many=True).data
        })

    def put(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'phone_number' in serializer.validated_data:
            request.user.username = serializer.validated_data['phone_number']

        serializer.save()
        return Response({
            'user': UserSerializer(request.user, context={'request': request}).data,
            'message': 'Profile updated successfully'
        })

    def patch(self, request):
        order_id = request.data.get('order_id')

        if not order_id:
            return Response({"error": "Order id is require to update an order"}, status=status.HTTP_400_BAD_REQUEST)
        
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        
        if order.status not in ['pending', 'preparing']:
            return Response({"error": f"Cannot update order. Order status is {order.status}"}, status=status.HTTP_400_BAD_REQUEST)
        
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
                    pricing.purchase_price if order.order_type == 'purchase' else pricing.refill_price
                )
                order.total_amount = unit_price * order.quantity
            except Pricing.DoesNotExist:
                return Response({"error": "Error updating order"})
            
        for field in ['delivery_address', 'delivery_notes']:
            if field in data:
                setattr(order, field, data[field])

        order.save()
        return Response({
            'order': OrderSerializer(order).data,
            'message': "Order updated successfully!"
        })
    
    def delete(self, request):
        if request.user.profile_picture:
            request.user.profile_picture.delete(save=True)
            return Response({"message": "Profile removed successfully"})
        return Response({
            "error": "No profile picture to remove"
        }, status=status.HTTP_400_BAD_REQUEST)

class AdminUserListView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        
        # Search filter
        search = request.query_params.get('search')
        if search:
            users = users.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        # Role filter
        role = request.query_params.get('role')
        if role == 'staff':
            users = users.filter(groups__name='staff')
        elif role == 'customer':
            users = users.filter(groups__name='customers')
        
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response({
            'count': users.count(),
            'results': serializer.data
        })
    
    def put(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if request.user.id == user.id and 'role'  in request.data:
            return Response({"error": "You cannot change your own role!"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data

        if 'first_name' in data:
            if not data['first_name'] or not data['first_name'].strip():
                return Response({"first_name": "First name is required"}, status=status.HTTP_400_BAD_REQUEST)
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            if not data['last_name'] or not data['last_name'].strip():
                return Response({"last_name": "Last name is required"}, status=status.HTTP_400_BAD_REQUEST)
            user.first_name = data['last_name'].strip()
        
        if 'role' in data:
            role = data['role']
            if role not in ['staff', 'customer']:
                return Response(
                    {"role": ["Role must be 'staff' or 'customer'."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            staff_group = Group.objects.get(name='staff')
            customer_group = Group.objects.get(name='customers')

            if role == 'staff':
                user.groups.add(staff_group)
                user.groups.remove(customer_group)
            else:
                user.groups.add(customer_group)
                user.groups.remove(staff_group)

        user.save()
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'message': f'User "{user.first_name} {user.last_name}" updated successfully.'
            })
    
    def delete(self, request, pk):
        if request.user.id == pk:
            return Response(
                {"error": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, pk=pk)
        user.is_active = False
        user.groups.clear()
        user.save()

        return Response({
            'message': f'User "{user.first_name} {user.last_name}" has been deactivated.'
        })
    
class AdminDashboardView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        # ── Orders Stats ──
        total_orders = Order.objects.count()
        orders_by_status = dict(
            Order.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        total_order_revenue = Order.objects.filter(status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # ── Users Stats ──
        total_users = User.objects.filter(is_active=True).count()
        staff_group = Group.objects.filter(name='staff').first()
        customer_group = Group.objects.filter(name='customers').first()

        total_staff = User.objects.filter(groups=staff_group, is_active=True).count() if staff_group else 0
        total_customers = User.objects.filter(groups=customer_group, is_active=True).count() if customer_group else 0

        seven_days_ago = timezone.now() - timedelta(days=7)
        new_users_week = User.objects.filter(date_joined__gte=seven_days_ago, is_active=True).count()

        # ── Bottles Stats ──
        total_bottles = Bottle.objects.count()
        active_bottles = Bottle.objects.filter(is_active=True).count()
        inactive_bottles = Bottle.objects.filter(is_active=False).count()
        bottles_by_size = dict(
            Bottle.objects.values('size').annotate(count=Count('id')).values_list('size', 'count')
        )
        active_by_size = dict(
            Bottle.objects.filter(is_active=True).values('size').annotate(count=Count('id')).values_list('size', 'count')
        )

        # ── Payments Stats ──
        total_payments = Payment.objects.count()
        total_payment_amount = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        completed_payments = Payment.objects.filter(status='completed').count()
        completed_payment_amount = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        pending_payments = Payment.objects.filter(status='pending').count()
        failed_payments = Payment.objects.filter(status='failed').count()

        # ── Pricings ──
        pricings = Pricing.objects.all()
        pricing_list = PricingSerializer(pricings, many=True).data

        return Response({
            'orders': {
                'total': total_orders,
                'by_status': {
                    'pending': orders_by_status.get('pending', 0),
                    'paid': orders_by_status.get('paid', 0),
                    'preparing': orders_by_status.get('preparing', 0),
                    'dispatched': orders_by_status.get('dispatched', 0),
                    'completed': orders_by_status.get('completed', 0),
                    'cancelled': orders_by_status.get('cancelled', 0),
                },
                'completed_revenue': str(total_order_revenue),
            },
            'users': {
                'total': total_users,
                'staff': total_staff,
                'customers': total_customers,
                'new_this_week': new_users_week,
            },
            'bottles': {
                'total': total_bottles,
                'active': active_bottles,
                'inactive': inactive_bottles,
                'by_size': {
                    '5L': bottles_by_size.get(5, 0),
                    '10L': bottles_by_size.get(10, 0),
                    '20L': bottles_by_size.get(20, 0),
                },
                'active_by_size': {
                    '5L': active_by_size.get(5, 0),
                    '10L': active_by_size.get(10, 0),
                    '20L': active_by_size.get(20, 0),
                },
            },
            'payments': {
                'total': total_payments,
                'total_amount': str(total_payment_amount),
                'completed': completed_payments,
                'completed_amount': str(completed_payment_amount),
                'pending': pending_payments,
                'failed': failed_payments,
            },
            'pricings': pricing_list,
        })