from rest_framework import serializers
from .models import User, LocationHistory


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'phone_number',
                  'address', 'location_lat', 'location_lng', 'location_updated_at',
                  'is_rider', 'is_admin']
        extra_kwargs = {'password': {'write_only': True}}


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['phone_number', 'first_name', 'last_name', 'address', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['phone_number'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            address=validated_data['address'],
            password=validated_data['password']
        )
        return user


class LocationUpdateSerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6)
    accuracy = serializers.FloatField(required=False, allow_null=True)
    speed = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.FloatField(required=False, allow_null=True)


class LocationHistorySerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = LocationHistory
        fields = ['id', 'user', 'user_details', 'lat', 'lng', 'accuracy',
                  'speed', 'heading', 'timestamp']