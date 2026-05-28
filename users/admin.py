from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, LocationHistory


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['phone_number', 'first_name', 'last_name', 'is_rider', 'is_admin',
                    'location_lat', 'location_lng', 'location_updated_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('phone_number', 'address', 'location_lat', 'location_lng',
                       'location_updated_at', 'is_rider', 'is_admin')
        }),
    )


@admin.register(LocationHistory)
class LocationHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'lat', 'lng', 'accuracy', 'speed', 'timestamp']
    list_filter = ['user']