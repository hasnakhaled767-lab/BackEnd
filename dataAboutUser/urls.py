from django.urls import path
from . import views

urlpatterns = [
    path('foods/', views.FoodList.as_view(), name='food-list'), 
    path('api/alternatives/', views.get_alternatives_api, name='alternatives_api'),
    path('api/signup/', views.signup_api, name='signup_api'),
    path('api/login/', views.login_api, name='login_api'),
    path('create_scan_api/', views.CreateScanAPI.as_view()),
    path('api/profile/update/<int:user_id>/', views.update_health_profile, name='update_profile'),
]




