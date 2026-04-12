from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

# استيراد الموديلات
from .models import Food, FoodAlternative, HealthProfile, ScanHistory

# استيراد السيريالايزر - ضفنا HealthProfileSerializer هنا
from .serializers import (
    FoodAlternativeSerializer, 
    UserSerializer, 
    ScanHistorySerializer, 
    HealthProfileSerializer
)
# 1. وظيفة لعرض سجل الفحوصات (Web)
@login_required
def scan_list(request):
    # التصحيح هنا: order_by وليس order_get
    scans = ScanHistory.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'scan_list.html', {'scans': scans})

# 2. وظيفة تجريبية لإضافة فحص (Web)
@login_required
def add_test_scan(request):
    if request.method == "POST":
        ScanHistory.objects.create(
            user=request.user,
            detected_food="تفاح أخضر",
            ai_analysis="هذه الفاكهة غنية بالألياف ومناسبة لحالتك الصحية.",
            image=request.FILES.get('food_image')
        )
        return redirect('scan_list')
    return render(request, 'add_scan.html')

from rest_framework import generics
from .models import Food
from .serializers import FoodSerializer

class FoodList(generics.ListCreateAPIView):
    queryset = Food.objects.all()
    serializer_class = FoodSerializer

@api_view(['GET'])
def get_alternatives_api(request):
    alternatives = FoodAlternative.objects.all()
    serializer = FoodAlternativeSerializer(alternatives, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def signup_api(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        # بنسيف اليوزر الجديد
        user = serializer.save()
        # بنعمله بروفايل صحي مربوط بيه عشان يسيف فيه طوله ووزنه بعدين
        HealthProfile.objects.create(user=user)
        return Response({
            "message": "User created successfully!",
            "user_id": user.id
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API تسجيل الدخول
@api_view(['POST'])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    
    if user is not None:
        return Response({"message": "Login successful!", "user_id": user.id}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    




@api_view(['POST'])
def create_scan_api(request):
    food_name = request.data.get('food_name')
    user_id = request.data.get('user_id')
    
    try:
        user = User.objects.get(id=user_id)
        # بندور على الأكلة في جدول الـ Food
        food_obj = Food.objects.filter(name__iexact=food_name).first()
        
        # بنخزن في الـ ScanHistory بالأسماء اللي إنتِ كاتباها في الـ Model
        scan = ScanHistory.objects.create(
            user=user,
            food=food_obj, # ده الـ ForeignKey للأكلة
            detected_food_name=food_name # ده الاسم اللي إنتِ مسمياه
        )
        
        return Response({
            "scan_id": scan.id,
            "detected_food": food_name,
            "calories": food_obj.calories if food_obj else "Unknown",
            "message": "Scan recorded successfully!"
        }, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST', 'PUT'])
def update_health_profile(request, user_id):
    try:
        profile = HealthProfile.objects.get(user_id=user_id)
        data = request.data
        
        # تحويل البيانات لأرقام عشان نعرف نحسب
        weight = float(data.get('weight', profile.weight or 0))
        height_cm = float(data.get('height', profile.height or 0))
        age = int(data.get('age', profile.age or 0))
        gender = data.get('gender', profile.gender)
        
        # حساب الـ BMI
        bmi = 0
        if height_cm > 0:
            height_m = height_cm / 100
            bmi = round(weight / (height_m ** 2), 1)

        # حساب السعرات (BMR)
        if gender == 'Male':
            bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) - 161
        
        daily_goal = int(bmr * 1.5) # بافتراض نشاط متوسط

        serializer = HealthProfileSerializer(profile, data=data, partial=True)
        if serializer.is_valid():
            serializer.save(daily_calories_goal=daily_goal)
            return Response({
                "message": "Success!",
                "bmi": bmi,
                "daily_goal": daily_goal,
                "details": serializer.data
            })
        return Response(serializer.errors, status=400)
        
    except HealthProfile.DoesNotExist:
        return Response({"error": "Profile not found"}, status=404)