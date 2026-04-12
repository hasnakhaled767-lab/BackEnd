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

class ScanHistorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True) # السطر ده هو "كلمة السر" للزرار

    class Meta:
        model = ScanHistory
        fields = ['user', 'detected_food_name', 'image']

# 5. سيرياليزر الملف الصحي (اللي ضفنا فيه الحقول الجديدة)
class HealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProfile
        fields = [
            'id', 'user', 'height', 'weight', 'age', 'gender', 
            'daily_calories_goal', 'has_diabetes', 
            'has_blood_pressure', 'food_allergies', 'chronic_diseases'
        ]