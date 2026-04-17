from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Food, FoodAlternative, HealthProfile, ScanHistory

from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework import serializers


# 1. سيرياليزر المستخدم (للتسجيل والدخول)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

# 2. سيرياليزر الأطعمة
class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = '__all__'

# 3. سيرياليزر البدائل الصحية
class FoodAlternativeSerializer(serializers.ModelSerializer):
    original_food = FoodSerializer(read_only=True)
    suggested_alternative = FoodSerializer(read_only=True)

    class Meta:
        model = FoodAlternative
        fields = ['original_food', 'suggested_alternative', 'reason_why']

class ScanHistorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True) # السطر ده هو "كلمة السر" للزرار

    class Meta:
      model = ScanHistory
      
      fields = [
            'id', 'food_name', 'image', 'scan_date', 
            'is_healthy', 'suggested_alternative', 
            'calories', 'protein', 'carbs', 'fats'
        ]
      read_only_fields = ['scan_date', 'calories', 'protein', 'carbs', 'fats', 'is_healthy', 'user', 'suggested_alternative']
      
class HealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProfile
        fields = [
            'user', 'height', 'weight', 'age', 'gender',
            'has_diabetes', 'has_blood_pressure', 'has_lactose_allergy'
        ]
        

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        # التأكد من تطابق كلمتي المرور الجديدتين
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "كلمة المرور الجديدة غير متطابقة."})
        return data