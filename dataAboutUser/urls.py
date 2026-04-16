from django.urls import path
from . import views

urlpatterns = [
    # 1. حسابات المستخدمين
    path('signup/', views.signup_api, name='signup_api'),
    path('login/', views.login_api, name='login_api'),
    path('change-password/', views.change_password, name='change_password'),

    # 2. البيانات الصحية (البروفايل)
    path('profile/update/<int:user_id>/', views.update_health_profile, name='update_health_profile'),

    # 3. الـ Scan والتحليل
    path('create_scan_api/', views.CreateScanAPI.as_view(), name='create_scan_api'),
    
    # 4. الأكلات والبدائل
    path('foods/', views.FoodList.as_view(), name='food_list'),
    path('alternatives/', views.get_alternatives_api, name='get_alternatives_api'),
]