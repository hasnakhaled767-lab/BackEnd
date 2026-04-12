from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Food, FoodAlternative, HealthProfile, ScanHistory

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

# 4. سيرياليزر تاريخ المسح (الاسكان)
class ScanHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanHistory
        fields = ['id', 'user', 'detected_food', 'ai_analysis', 'image', 'created_at']

# 5. سيرياليزر الملف الصحي (اللي ضفنا فيه الحقول الجديدة)
class HealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProfile
        fields = [
            'id', 'user', 'height', 'weight', 'age', 'gender', 
            'daily_calories_goal', 'has_diabetes', 
            'has_blood_pressure', 'food_allergies', 'chronic_diseases'
        ]