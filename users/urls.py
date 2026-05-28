from django.urls import path
from users.views import *

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('location/update/', UpdateLocationView.as_view(), name='update-location'),
    path('location/me/', GetUserLocationView.as_view(), name='my-location'),
    path('location/user/<int:user_id>/', GetUserLocationView.as_view(), name='user-location'),
    path('location/history/', LocationHistoryView.as_view(), name='location-history'),
    path('location/history/<int:user_id>/', LocationHistoryView.as_view(), name='user-location-history'),
]