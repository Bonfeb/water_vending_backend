from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils import timezone

from users.models import *
from users.serializers import *

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone_number')
        password = request.data.get('password')

        try:
            user = User.objects.get(phone_number=phone)
            user = authenticate(username=user.username, password=password)
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data
                })
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response({'message': 'Logged out successfully'})


class ProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateLocationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LocationUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        request.user.location_lat = data['lat']
        request.user.location_lng = data['lng']
        request.user.location_updated_at = timezone.now()
        request.user.save()

        LocationHistory.objects.create(
            user=request.user,
            lat=data['lat'],
            lng=data['lng'],
            accuracy=data.get('accuracy'),
            speed=data.get('speed'),
            heading=data.get('heading')
        )

        return Response({
            'message': 'Location updated',
            'lat': str(data['lat']),
            'lng': str(data['lng']),
            'timestamp': request.user.location_updated_at
        })


class GetUserLocationView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id=None):
        if user_id:
            user = get_object_or_404(User, pk=user_id)
        else:
            user = request.user

        return Response({
            'user_id': user.id,
            'name': f"{user.first_name} {user.last_name}",
            'phone': user.phone_number,
            'lat': str(user.location_lat) if user.location_lat else None,
            'lng': str(user.location_lng) if user.location_lng else None,
            'updated_at': user.location_updated_at,
            'is_rider': user.is_rider
        })


class LocationHistoryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id=None):
        from core.permissions import IsAdmin
        if request.user.is_admin and user_id:
            user = get_object_or_404(User, pk=user_id)
        else:
            user = request.user

        history = LocationHistory.objects.filter(user=user)[:50]
        serializer = LocationHistorySerializer(history, many=True)
        return Response(serializer.data)