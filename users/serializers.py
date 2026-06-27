from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import *
from core.utils import standardize_phone_number


class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.ReadOnlyField()
    is_customer = serializers.ReadOnlyField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'phone_number',
            'profile_picture','is_admin', 
            'is_customer',
            'is_superuser'
        ]

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)
    phone_number = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = ['phone_number', 'first_name', 'last_name', 'password']

    def validate_phone_number(self, value):
        try:
            standardized = standardize_phone_number(value)
        except ValueError:
            raise serializers.ValidationError(
                "Invalid phone number. Use format 0712345678 or +254712345678"
            )
        if User.objects.filter(phone_number=standardized).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return standardized

    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required.")
        return value.strip()

    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required.")
        return value.strip()

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['phone_number'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=20, required=False)
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'profile_picture',
        ]

    def validate_phone_number(self, value):
        try:
            standardized = standardize_phone_number(value)
        except ValueError:
            raise serializers.ValidationError(
                "Invalid phone number. Use format 0712345678 or +254712345678"
            )
        user = self.instance
        if User.objects.filter(phone_number=standardized).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return standardized


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)

    def validate_phone_number(self, value):
        try:
            return standardize_phone_number(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))