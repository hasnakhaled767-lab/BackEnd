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
@permission_classes([IsAuthenticated])  # مهم جداً عشان التوكين يشتغل
def update_health_profile(request):  # شلنا الـ user_id من هنا نهائياً
    try:
        # 1. بنجيب بيانات اليوزر من التوكين أوتوماتيك
        user = request.user
        
        # 2. نسخة قابلة للتعديل من البيانات المبعوثة
        data = request.data.copy()

        # 3. البحث عن بروفايل اليوزر أو إنشاؤه لو مش موجود
        profile, created = HealthProfile.objects.get_or_create(user=user)

        # 4. تمرير البيانات للسيرياليزر للتحديث
        serializer = HealthProfileSerializer(profile, data=data, partial=True)

        if serializer.is_valid():
            # حفظ البيانات الصحية
            updated_profile = serializer.save()

            # حساب الهدف اليومي (BMR * 1.2)
            # تأكدي إن bmr_value معرفة كميثود أو بروبرتي في الموديل عندك
            daily_goal = round(updated_profile.bmr_value * 1.2)

            return Response({
                "status": "success",
                "message": "تم تحديث البيانات الصحية بنجاح!",
                "results": {
                    "bmi": updated_profile.bmi_value,
                    "bmi_status": updated_profile.bmi_status,
                    "bmr_basic": updated_profile.bmr_value,
                    "daily_calories_goal": daily_goal,
                },
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateScanAPI(generics.CreateAPIView):
    queryset = ScanHistory.objects.all()
    serializer_class = ScanHistorySerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        user = request.user 
        food_name_input = request.data.get('food_name', '').lower().strip()

        if not image_file:
            return Response({"error": "يرجى إرسال الصورة"}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_anonymous:
            return Response({"error": "يجب تسجيل الدخول أولاً"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = HealthProfile.objects.filter(user=user).first()
            food_item = Food.objects.filter(name__iexact=food_name_input).first()

            if not food_item:
                return Response({"error": "هذا الطعام غير مسجل في قاعدة البيانات"}, status=status.HTTP_404_NOT_FOUND)

            is_safe = True
            reasons = []
            suggested_alternative = None

            # --- قوائم المنع والبدايل لكل حالة ---
            
            # 1. مرض السكر
            diabetes_map = {
                'pancakes': 'بان كيك الشوفان بدون سكر',
                'waffles': 'وافل بدقيق اللوز',
                'ice cream': 'زبادي يوناني مثلج بالفواكه',
                'pizza': 'بيتزا بعجينة الشوفان وخضروات',
                'grapes': 'فراولة أو توت (مؤشر جلايسيمي منخفض)',
                'mango': 'تفاح أخضر',
                'pineapple': 'كمثرى',
                'watermelon': 'كانتالوب'
            }

            # 2. مرض الضغط
            pressure_map = {
                'bacon': 'صدور ديك رومي مشوية',
                'sausage': 'قطع دجاج مشوية',
                'hot dogs': 'سمك مشوي',
                'steak': 'لحم أحمر خالي من الدهون',
                'burgers': 'برجر دجاج منزلي مشوي',
                'pizza': 'بيتزا منزلية بجبنة قليلة الملح',
                'french fries': 'بطاطس ودجز مشوية في الفرن',
                'shrimp': 'سمك فيليه مشوي'
            }

            # 3. حساسية اللاكتوز
            lactose_map = {
                'ice cream': 'آيس كريم حليب جوز الهند أو اللوز',
                'milkshakes': 'سموثي فواكه بحليب الشوفان',
                'pancakes': 'بان كيك مخبوز بزيت جوز الهند',
                'waffles': 'وافل نباتي (Vegan)',
                'pizza': 'بيتزا بدون جبنة أو بجبنة نباتية',
                'cheese': 'لبنة خالية من اللاكتوز أو جبنة لوز'
            }

            if profile:
                # فحص السكر
                if profile.has_diabetes and food_name_input in diabetes_map:
                    is_safe = False
                    reasons.append("غير مناسب لمريض السكر (سكريات/نشويات عالية)")
                    suggested_alternative = diabetes_map[food_name_input]
                
                # فحص الضغط
                if profile.has_blood_pressure and food_name_input in pressure_map:
                    is_safe = False
                    reasons.append("غير مناسب لمريض الضغط (أملاح/دهون عالية)")
                    if not suggested_alternative: # لو ملوش بديل سكر ناخد بديل الضغط
                        suggested_alternative = pressure_map[food_name_input]
                
                # فحص اللاكتوز
                if profile.has_lactose_allergy and food_name_input in lactose_map:
                    is_safe = False
                    reasons.appendreasons.append("يحتوي على لاكتوز وأنت تعاني من حساسية تجاهه")
                    if not suggested_alternative:
                        suggested_alternative = lactose_map[food_name_input]

            # 4. صياغة النصيحة
            if is_safe:
                msg = f"المنتج ({food_item.name}) مناسب وآمن لحالتك الصحية."
            else:
                msg = f"تحذير طبي بخصوص ({food_item.name}): " + " و ".join(reasons)

            # 5. حفظ السجل
            scan_record = ScanHistory.objects.create(
                user=user,
                food_name=food_item.name,
                calories=food_item.calories,
                protein=food_item.protein,
                carbs=food_item.carbs,
                fats=food_item.fats,
                is_healthy=is_safe,
                image=image_file,
                suggested_alternative=suggested_alternative
            )

            # 6. الرد النهائي بالبديل الصحي
            return Response({
                "status": "success",
                "message": "تم تحليل الطعام بنجاح",
                "health_advice": msg,
                "suggested_alternative": suggested_alternative, # البديل هيظهر هنا
                "scan_details": {
                    "id": scan_record.id,
                    "image_url": scan_record.image.url if scan_record.image else None,
                    "date": scan_record.scan_date.strftime("%Y-%m-%d %H:%M")
                },
                "nutrition_facts": {
                    "calories": scan_record.calories,
                    "protein": scan_record.protein,
                    "carbs": scan_record.carbs,
                    "fats": scan_record.fats
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
    


# في views.py (تأكدي إن ده بس اللي موجود للهيستوري)
class UserScanHistoryList(generics.ListAPIView):
    serializer_class = ScanHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # بنستخدم scan_date عشان هو ده اللي موجود في الموديل عندك فعلاً
        return ScanHistory.objects.filter(user=self.request.user).order_by('-scan_date')
    