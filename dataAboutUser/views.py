from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import update_session_auth_hash
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# استيراد الموديلات والسيريالايزر
from .models import Food, FoodAlternative, HealthProfile, ScanHistory
from .serializers import (
    FoodAlternativeSerializer, 
    UserSerializer, 
    ScanHistorySerializer, 
    HealthProfileSerializer,
    FoodSerializer,
    ChangePasswordSerializer,
)

# --- 1. APIs الحسابات (Signup & Login) ---

@api_view(['POST'])
def signup_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if not username or not password:
        return Response({"error": "الاسم والباسورد مطلوبين"}, status=400)

    try:
        # 1. إنشاء اليوزر
        user = User.objects.create_user(username=username, password=password, email=email)
        
        # 2. إنشاء بروفايل صحي "فاضي" مرتبط باليوزر ده
        # هيتسيف عادي لأننا خلينا الحقول null=True
        HealthProfile.objects.create(user=user)

        return Response({
            "status": "success",
            "message": "تم إنشاء الحساب بنجاح! يمكنك الآن إكمال بياناتك الصحية."
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=400)
    
    
@api_view(['POST'])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        return Response({"message": "Login successful!", "user_id": user.id}, status=200)
    return Response({"error": "Invalid credentials"}, status=401)
@api_view(['POST', 'PUT'])
def update_health_profile(request, user_id):
    try:
        profile = HealthProfile.objects.get(user_id=user_id)
        
        # نسخة قابلة للتعديل من البيانات المبعوتة
        data = request.data.copy()

        serializer = HealthProfileSerializer(profile, data=data, partial=True)
        
        if serializer.is_valid():
            # حفظ البيانات (طول، وزن، إلخ)
            updated_profile = serializer.save()

            # حساب الهدف اليومي (BMR * 1.2)
            # بنستخدم الـ property اللي في الموديل مباشرة
            daily_goal = round(updated_profile.bmr_value * 1.2)
            
            return Response({
                "status": "success",
                    "message": "تم تحديث البيانات الصحية بنجاح!",       
                    "results": {
                    "bmi": updated_profile.bmi_value,
                    "bmi_status": updated_profile.bmi_status,
                    "bmr_basic": updated_profile.bmr_value,
                    "daily_calories_goal": daily_goal, # ده الهدف اللي هيظهر في الـ App
                },
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except HealthProfile.DoesNotExist:
        return Response({"error": "البروفايل غير موجود"}, status=404)
# --- 3. الـ API الأساسي للـ Scan والتحليل (مع زرار الرفع) ---


class CreateScanAPI(generics.CreateAPIView):
    queryset = ScanHistory.objects.all()
    serializer_class = ScanHistorySerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        # 1. حفظ بيانات السكان الأساسية
        response = super().create(request, *args, **kwargs)
        user_id = request.data.get('user')
        food_name = request.data.get('detected_food_name', '').lower().strip()

        try:
            profile = HealthProfile.objects.filter(user_id=user_id).first()
            food_item = Food.objects.filter(name__iexact=food_name).first()

            is_safe = True
            reasons = []

            # --- مجموعات الأكلات الطبية بناءً على لستة الداتابيز ---
            diabetes_list = ['pancakes', 'waffles', 'ice cream', 'milkshakes', 'pizza', 'grapes', 'mango', 'pineapple', 'watermelon']
            pressure_list = ['bacon', 'sausage', 'hot dogs', 'steak', 'burgers', 'pizza', 'french fries', 'shrimp']
            lactose_list = ['ice cream', 'milkshakes', 'pancakes', 'waffles', 'pizza', 'cheese'] # مجموعة اللاكتوز

            if profile:
                # فحص السكري
                if profile.has_diabetes and food_name in diabetes_list:
                    is_safe = False
                    reasons.append("غير مناسب لمريض السكر (سكريات/نشويات عالية)")

                # فحص الضغط
                if profile.has_blood_pressure and food_name in pressure_list:
                    is_safe = False
                    reasons.append("غير مناسب لمريض الضغط (املاح/دهون عالية)")

                # فحص حساسية اللاكتوز
                if profile.has_lactose_allergy and food_name in lactose_list:
                    is_safe = False
                    reasons.append("يحتوي على لاكتوز (ألبان) وأنت تعاني من حساسية تجاهه")

            # صياغة الرسالة النهائية
            if is_safe:
                msg = f"المنتج ({food_name}) مناسب وآمن لحالتك الصحية."
            else:
                msg = f"تحذير طبي بخصوص ({food_name}): { ' و '.join(reasons) }"

            # إضافة معلومات الـ BMI و الـ BMR للرد
            health_summary = ""
            if profile:
                health_summary = (f"مؤشر كتلة الجسم: {profile.bmi_value} ({profile.bmi_status}) | "
                                 f" احتياجك اليومي للسعرات: {profile.bmr_value} سعرة.")

            return Response({
                "status": "success",
                "is_safe": is_safe,
                "analysis_result": msg,
                "health_metrics": health_summary,
                "image_url": response.data.get('image'),
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=400)

class FoodList(generics.ListCreateAPIView):
    queryset = Food.objects.all()
    serializer_class = FoodSerializer

@api_view(['GET'])
def get_alternatives_api(request):
    alternatives = FoodAlternative.objects.all()
    serializer = FoodAlternativeSerializer(alternatives, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated]) # لازم يكون عامل login عشان يغير الباسورد
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        user = request.user
        # التأكد إن الباسورد القديم صح
        if not user.check_password(serializer.data.get("old_password")):
            return Response({"old_password": ["كلمة المرور القديمة غير صحيحة."]}, status=400)
        
        # تغيير الباسورد
        user.set_password(serializer.data.get("new_password"))
        user.save()
        
        # تحديث الجلسة عشان ميعملش logout تلقائي بعد التغيير
        update_session_auth_hash(request, user)
        
        return Response({"status": "success", "message": "تم تغيير كلمة المرور بنجاح!"}, status=200)

    return Response(serializer.errors, status=400)