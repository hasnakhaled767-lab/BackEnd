from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser

# استيراد الموديلات والسيريالايزر
from .models import Food, FoodAlternative, HealthProfile, ScanHistory
from .serializers import (
    FoodAlternativeSerializer, 
    UserSerializer, 
    ScanHistorySerializer, 
    HealthProfileSerializer,
    FoodSerializer
)

# --- 1. APIs الحسابات (Signup & Login) ---

@api_view(['POST'])
def signup_api(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        HealthProfile.objects.create(user=user)
        return Response({"message": "User created!", "user_id": user.id}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        return Response({"message": "Login successful!", "user_id": user.id}, status=200)
    return Response({"error": "Invalid credentials"}, status=401)

# --- 2. تحديث البروفايل الصحي (اللي كان عامل Error) ---

@api_view(['POST', 'PUT'])
def update_health_profile(request, user_id):
    try:
        # بنجيب البروفايل بتاع اليوزر من الداتابيز
        profile = HealthProfile.objects.get(user_id=user_id)
        
        # بنسحب البيانات اللي اليوزر بعتها في الـ Swagger
        weight = float(request.data.get('weight', profile.weight or 0))
        height = float(request.data.get('height', profile.height or 0))
        age = int(request.data.get('age', profile.age or 0))
        gender = request.data.get('gender', profile.gender)

        # الحسبة البرمجية للسعرات (Mifflin-St Jeor Equation)
        if weight > 0 and height > 0 and age > 0:
            if gender == 'Male':
                # معادلة الرجالة
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
            else:
                # معادلة الستات
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
            
            # بنحدث القيمة في الـ request قبل ما نبعتها للمترجم (Serializer)
            # ضربنا في 1.2 عشان ده معدل النشاط الطبيعي
            request.data['daily_calories_goal'] = round(bmr * 1.2)

        # بنبعت الداتا للمترجم عشان يتأكد إنها صح ويسيفها
        serializer = HealthProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "تم تحديث البيانات وحساب السعرات الحرارية بنجاح!",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except HealthProfile.DoesNotExist:
        return Response({"error": "البروفايل ده مش موجود"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# --- 3. الـ API الأساسي للـ Scan والتحليل (مع زرار الرفع) ---

class CreateScanAPI(generics.CreateAPIView):
    queryset = ScanHistory.objects.all()
    serializer_class = ScanHistorySerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        # 1. حفظ البيانات الأساسية (اليوزر، الصورة، الاسم)
        response = super().create(request, *args, **kwargs)
        user_id = request.data.get('user')
        food_name = request.data.get('detected_food_name', '').lower().strip()

        try:
            profile = HealthProfile.objects.filter(user_id=user_id).first()
            food_item = Food.objects.filter(name__iexact=food_name).first()

            is_safe = True
            reasons = []

            # --- تقسيم المجموعات بناءً على اللستة اللي بعتيها ---
            
            # 1. مجموعة السكري (سكريات عالية + نشويات)
            diabetes_danger_list = [
                'pancakes', 'waffles', 'ice cream', 'milkshakes', 'pizza', 'spaghetti', 
                'macaroni', 'potato', 'potato wedges', 'french fries', 'beer',
                'mango', 'pineapple', 'grapes', 'cherry', 'durian', 'watermelon', 'apple'
            ]

            # 2. مجموعة الضغط (أملاح عالية + دهون مشبعة)
            pressure_danger_list = [
                'bacon', 'sausage', 'hot dogs', 'steak', 'barbecue ribs', 'meatloaf',
                'hamburgers', 'pizza', 'fried chicken', 'tacos', 'french fries', 
                'potato wedges', 'shrimp', 'beer'
            ]

            if profile:
                # فحص مريض السكر
                if profile.has_diabetes and food_name in diabetes_danger_list:
                    is_safe = False
                    reasons.append("غير مناسب لمريض السكر (نسبة سكر أو نشويات عالية)")

                # فحص مريض الضغط
                if profile.has_blood_pressure and food_name in pressure_danger_list:
                    is_safe = False
                    reasons.append("غير مناسب لمريض الضغط (نسبة أملاح أو دهون عالية)")

                # فحص الحساسية (لو المكون موجود في اسم الأكلة)
                if profile.food_allergies:
                    allergies = [a.strip().lower() for a in profile.food_allergies.split(',')]
                    for allergy in allergies:
                        if allergy in food_name:
                            is_safe = False
                            reasons.append(f"يحتوي على مكونات تسبب لك حساسية ({allergy})")

            # صياغة الرد النهائي
            if is_safe:
                msg = f"المنتج ({food_name}) آمن ومناسب لحالتك الصحية"
            else:
                msg = f"تحذير طبي: {food_name} قد يكون { ' و '.join(reasons) }"

            # حساب عدد السكاني لليوزر
            scan_count = ScanHistory.objects.filter(user_id=user_id).count()

            return Response({
                "status": "success",
                "is_safe": is_safe,
                "analysis_result": msg,
                "scan_count": scan_count,
                "image_url": response.data.get('image'),
            }, status=201)

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