from django.contrib import admin
from users.models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'phone_number', 'is_active']
    search_fields = ['phone_number', 'first_name', 'last_name']