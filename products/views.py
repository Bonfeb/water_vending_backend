from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from core.permissions import IsStaffMember
from products.models import Bottle, Pricing
from products.serializers import *

class PublicPricingListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        pricing = Pricing.objects.all()
        serializer = PricingSerializer(pricing, many=True)
        return Response(serializer.data)

class PublicBottleSizesView(APIView):
    """Public: List available bottle sizes for the order form."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        sizes = [
            {'value': choice[0], 'label': choice[1]}
            for choice in Bottle.SIZE_CHOICES
        ]
        return Response(sizes)

class PublicInventoryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        inventory = []
        for size_value, size_label in Bottle.SIZE_CHOICES:
            count = Bottle.objects.filter(size=size_value, is_active=True).count()
            inventory.append({
                'size': size_value,
                'label': size_label,
                'in_stock': count > 0,
                'available_count': count
            })
        return Response(inventory)

class AdminBottleListCreateView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        bottles = Bottle.objects.all()

        user_id = request.query_params.get('user_id')
        size = request.query_params.get('size')
        is_active = request.query_params.get('is_active')
        unassigned = request.query_params.get("unassigned")

        if user_id:
            bottles = bottles.filter(user_id=user_id)
        if size:
            bottles = bottles.filter(size=int(size))
        if is_active is not None:
            bottles = bottles.filter(is_active=(is_active.lower() == 'true'))
        if unassigned == "true":
            bottles = bottles.filter(user__isnull=True)

        serializer = BottleSerializer(bottles, many=True)
    
        summary = {
            "total_bottles": Bottle.objects.count(),
        "active_bottles": Bottle.objects.filter(
            is_active=True
        ).count(),
        "inactive_bottles": Bottle.objects.filter(
            is_active=False
        ).count(),
        "unassigned_bottles": Bottle.objects.filter(
            user__isnull=True
        ).count(),
        "by_size": {
            "5L": Bottle.objects.filter(size=5).count(),
            "10L": Bottle.objects.filter(size=10).count(),
            "20L": Bottle.objects.filter(size=20).count(),
        },
        }

        return Response({
            "summary": summary,
            "results": serializer.data
        })

    def post(self, request):
        serializer = BottleCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                BottleSerializer(serializer.instance).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminBottleDetailView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request, pk):
        bottle = get_object_or_404(Bottle, pk=pk)
        serializer = BottleSerializer(bottle)
        return Response(serializer.data)

    def put(self, request, pk):
        bottle = get_object_or_404(Bottle, pk=pk)
        serializer = BottleCreateSerializer(
            bottle, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(BottleSerializer(bottle).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        bottle = get_object_or_404(Bottle, pk=pk)
        bottle.is_active = False
        bottle.save()
        return Response({'message': 'Bottle sold/damaged'})

class AdminPricingListCreateView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        pricing = Pricing.objects.all()
        serializer = PricingSerializer(pricing, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PricingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminPricingDetailView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request, pk):
        pricing = get_object_or_404(Pricing, pk=pk)
        serializer = PricingSerializer(pricing)
        return Response(serializer.data)

    def put(self, request, pk):
        pricing = get_object_or_404(Pricing, pk=pk)
        serializer = PricingSerializer(pricing, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        pricing = get_object_or_404(Pricing, pk=pk)
        pricing.delete()
        return Response({'message': 'Pricing tier deleted'})

class CalculateTotalView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        order_type = request.data.get('order_type')
        size = request.data.get('size')
        quantity = request.data.get('quantity', 1)

        if not order_type or not size:
            return Response(
                {'error': 'order_type and size are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            size = int(size)
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response(
                {'error': 'size and quantity must be integers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pricing = Pricing.objects.get(size=size)
        except Pricing.DoesNotExist:
            return Response(
                {'error': f'No pricing found for {size}L size'},
                status=status.HTTP_404_NOT_FOUND
            )

        unit_price = (
            pricing.purchase_price if order_type == 'purchase'
            else pricing.refill_price
        )
        total = unit_price * quantity

        return Response({
            'order_type': order_type,
            'size': size,
            'size_display': pricing.get_size_display(),
            'quantity': quantity,
            'unit_price': str(unit_price),
            'total_amount': str(total),
            'currency': 'KES'
        })