from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from django.shortcuts import get_object_or_404

from core.permissions import permissions
from products.models import *
from products.serializers import *

class BottleListCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        bottles = Bottle.objects.filter(user=request.user, is_active=True)
        serializer = BottleSerializer(bottles, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_admin:
            return Response({'error': 'Only admins can register bottles'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BottleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.data.get('user_id'))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BottleDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        bottle = get_object_or_404(Bottle, pk=pk, user=request.user)
        serializer = BottleSerializer(bottle)
        return Response(serializer.data)

    def delete(self, request, pk):
        bottle = get_object_or_404(Bottle, pk=pk, user=request.user)
        bottle.is_active = False
        bottle.save()
        return Response({'message': 'Bottle deactivated'})


class PricingListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        pricing = Pricing.objects.all()
        serializer = PricingSerializer(pricing, many=True)
        return Response(serializer.data)


class CalculateTotalView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        order_type = request.data.get('order_type')
        size = int(request.data.get('size'))
        quantity = int(request.data.get('quantity', 1))

        try:
            pricing = Pricing.objects.get(size=size)
            if order_type == 'purchase':
                total = pricing.purchase_price * quantity
            else:
                total = pricing.refill_price * quantity

            return Response({
                'order_type': order_type,
                'size': size,
                'quantity': quantity,
                'unit_price': str(pricing.purchase_price if order_type == 'purchase' else pricing.refill_price),
                'total_amount': str(total)
            })
        except Pricing.DoesNotExist:
            return Response({'error': 'Pricing not found'}, status=status.HTTP_404_NOT_FOUND)