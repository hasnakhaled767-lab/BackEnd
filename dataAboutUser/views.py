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

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import update_session_auth_hash
from .serializers import ChangePasswordSerializer # تأكدي من عمل import
from rest_framework import generics, permissions # عشان يعرف permissions
from .models import ScanHistory
from .serializers import ScanHistorySerializer 
from rest_framework.authtoken.models import Token # ضيفي الـ Import ده فوق


# استيراد الموديلات والسيريالايزر
from .models import Food, FoodAlternative, HealthProfile, ScanHistory
from .serializers import (
    FoodAlternativeSerializer,
    UserSerializer,
    ScanHistorySerializer, # اتأكدي إن آخرها Serializer ومكتوبة صح
    HealthProfileSerializer,
    FoodSerializer,
    ChangePasswordSerializer,
)



@api_view(['POST'])
def signup_api(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password') # السطر الجديد

    # 1. التأكد إن كل الخانات مليانة
    if not username or not password or not confirm_password:
        return Response({"error": "يرجى ملء جميع الخانات المطلوبة"}, status=400)

    # 2. التأكد إن الباسورد متطابق (Confirm Password Logic)
    if password != confirm_password:
        return Response({"error": "كلمة المرور غير متطابقة، يرجى التأكد مرة أخرى"}, status=400)

    # 3. التأكد إن اليوزر مش موجود قبل كدة
    if User.objects.filter(username=username).exists():
        return Response({"error": "اسم المستخدم موجود بالفعل"}, status=400)

    # 4. إنشاء الحساب لو كله تمام
    user = User.objects.create_user(username=username, email=email, password=password)
    
    return Response({
        "status": "success",
        "message": "تم إنشاء حسابك بنجاح! يمكنك الآن تسجيل الدخول"
    }, status=201)
    

@api_view(['POST'])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        # البحث عن التوكين القديم أو إنشاء واحد جديد
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            "status": "success",
            "message": "تم تسجيل الدخول بنجاح",
            "token": token.key,  # ده السطر اللي الفرونت محتاجه
            "user_id": user.id,
            "username": user.username
        }, status=200)
    else:
        return Response({
            "status": "error",
            "message": "اسم المستخدم أو كلمة المرور غير صحيحة"
        }, status=401)
    



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
        
        image_file = request.FILES.get('image') 

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
                
              # 3. حفظ السجل في الهيستوري (تأكدي إن الأسماء مطابقة للموديل عندك)
            scan_record = ScanHistory.objects.create(
                user_id=user_id,
                food_name=food_item.name,
                calories=food_item.calories,
                protein=food_item.protein,
                carbs=food_item.carbs,
                fats=food_item.fats,
                is_healthy=food_item.is_healthy,
                image=image_file
            )
            
            
            return Response({
                "status": "success",
                "message": "تم تحليل الطعام بنجاح",
                "health_advice": msg,
                "scan_details": {
                    "id": scan_record.id,
                    "image_url": scan_record.image.url if scan_record.image else None,
                    "date": scan_record.scan_date.strftime("%Y-%m-%d %H:%M")
                },
                "nutrition_facts": {
                    "calories": scan_record.calories,
                    "protein": scan_record.protein,
                    "carbs": scan_record.carbs,
                    "fats": scan_record.fats,
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # الـ except لازم تكون على نفس مستوى الـ try
            return Response({"status": "error", "message": str(e)}, status=400)



class FoodList(generics.ListCreateAPIView):
    queryset = Food.objects.all()
    serializer_class = FoodSerializer

@api_view(['GET'])
def get_alternatives_api(request):
    alternatives = FoodAlternative.objects.all()
    serializer = FoodAlternativeSerializer(alternatives, many=True)
    return Response(serializer.data)




class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated] # لازم يكون مسجل دخول

    def get_object(self):
        return self.request.user # بيجيب اليوزر الحالي

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # 1. التأكد من الباسورد القديم
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["كلمة المرور القديمة غير صحيحة."]}, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. تغيير الباسورد وتشفيره
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            
            # 3. تحديث الجلسة عشان ميعملش logout
            update_session_auth_hash(request, self.object)
            
            return Response({"status": "success", "message": "تم تغيير كلمة المرور بنجاح!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ScanHistoryList(generics.ListAPIView):
    serializer_class = ScanHistorySerializer # غيري دي لـ ScanHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # غيري Scan لـ ScanHistory
        return ScanHistory.objects.filter(user=self.request.user).order_by('-created_at')
    

    