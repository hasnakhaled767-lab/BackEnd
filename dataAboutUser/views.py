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
        profile = HealthProfile.objects.get(user_id=user_id)
        serializer = HealthProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully!", "data": serializer.data})
        return Response(serializer.errors, status=400)
    except HealthProfile.DoesNotExist:
        return Response({"error": "Profile not found"}, status=404)

# --- 3. الـ API الأساسي للـ Scan والتحليل (مع زرار الرفع) ---

class CreateScanAPI(generics.CreateAPIView):
    queryset = ScanHistory.objects.all()
    serializer_class = ScanHistorySerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user_id = response.data.get('user')
        food_name = response.data.get('detected_food_name', '').lower() # حولناها لسمول للمقارنة
        
        try:
            profile = HealthProfile.objects.filter(user_id=user_id).first()
            food_data = Food.objects.filter(name__iexact=food_name).first()
            
            is_safe = True
            reasons = []

            if profile:
                # 1. فحص السكر والضغط (الأكواد القديمة)
                if food_data:
                    sugar = food_data.sugar_content or 0
                    if getattr(profile, 'has_diabetes', False) and sugar > 15:
                        is_safe = False
                        reasons.append("نسبة سكر عالية")

                    sodium = food_data.sodium_content or 0
                    if getattr(profile, 'has_blood_pressure', False) and sodium > 10:
                        is_safe = False
                        reasons.append("نسبة صوديوم عالية")

                # 2. فحص الحساسية (الجزء الجديد)
                # لو اليوزر كاتب في الحساسية "فراولة" واسم الأكلة فيها "فراولة"
                if profile.food_allergies:
                    allergy_list = profile.food_allergies.lower().split(',') # لو كاتب كذا حاجة بينهم فاصلة
                    for allergy in allergy_list:
                        if allergy.strip() in food_name:
                            is_safe = False
                            reasons.append(f"يحتوي على مكونات تسبب لك حساسية ({allergy.strip()})")

                # 3. فحص أمراض أخرى (مثلاً القولون العصبي)
                if getattr(profile, 'has_ibs', False): # لو ضفتِ حقل IBS في الموديل
                    if any(word in food_name for word in ['بقوليات', 'عدس', 'ثوم', 'بصل']):
                        is_safe = False
                        reasons.append("قد يهيج القولون العصبي")

            # صياغة الرسالة النهائية
            if is_safe:
                msg = f"هذا المنتج ({food_name}) مناسب لحالتك الصحية."
            else:
                msg = f"تحذير المنتج قد لا يناسبك لانه: {', '.join(reasons)}"

            return Response({
                "status": "success",
                "is_safe": is_safe,
                "analysis_result": msg,
                "scan_id": response.data.get('id'),
                "image_url": response.data.get('image')
            }, status=201)

        except Exception as e:
            return Response({"status": "partial_success", "message": str(e)}, status=201)
    

# --- 4. الأكلات والبدائل ---

class FoodList(generics.ListCreateAPIView):
    queryset = Food.objects.all()
    serializer_class = FoodSerializer

@api_view(['GET'])
def get_alternatives_api(request):
    alternatives = FoodAlternative.objects.all()
    serializer = FoodAlternativeSerializer(alternatives, many=True)
    return Response(serializer.data)