from django.urls import path
from users.views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('dashboard/', AdminDashboardView.as_view(), name='dashboard'),
    path('users/', AdminUserListView.as_view(), name='users'),
    path('users/<int:pk>/', AdminUserListView.as_view(), name='user_detail')
]