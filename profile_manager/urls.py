from django.urls import path
from django.contrib.auth.views import LogoutView

from profile_manager import views

urlpatterns = [
    # post views
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', views.list_of_profiles, name='list_of_profiles'),
    path('profiles/<int:user_id>/', views.get_concrete_profile, name='get_concrete_profile'),
    path('profiles/edit/', views.edit_profile, name='edit_profile'),
]