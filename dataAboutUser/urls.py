from django.urls import path
from . import views

urlpatterns = [
    path('foods/', views.food_list, name='food_list'),
    path('api/alternatives/', views.get_alternatives_api, name='alternatives_api'),
    path('api/signup/', views.signup_api, name='signup_api'),
    path('api/login/', views.login_api, name='login_api'),
    path('api/scan/create/', views.create_scan_api, name='create_scan_api'), # ده المهم للتجربة
    path('api/profile/update/<int:user_id>/', views.update_health_profile, name='update_profile'),
]