from rest_framework import serializers
from .models import Food, FoodAlternative, HealthProfile
from django.contrib.auth.models import User
from .models import HealthProfile
from .models import ScanHistory


class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = '__all__'

class FoodAlternativeSerializer(serializers.ModelSerializer):
    # بنجيب تفاصيل الأكلة الأصلية والبديلة كاملة مش بس الـ ID
    original_food = FoodSerializer(read_only=True)
    suggested_alternative = FoodSerializer(read_only=True)

    class Meta:
        model = FoodAlternative
        fields = ['original_food', 'suggested_alternative', 'reason_why']


        

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}} # عشان الباسورد ميرجعش في الـ API

    def create(self, validated_data):
        # إنشاء المستخدم وتشفير الباسورد أوتوماتيك
        user = User.objects.create_user(**validated_data)
        return user
    



class ScanHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanHistory
        fields = ['id', 'user', 'detected_food', 'ai_analysis', 'image', 'created_at']


        class HealthProfileSerializer(serializers.ModelSerializer):
            class Meta:
                model = HealthProfile
                fields = ['height', 'weight', 'age', 'gender', 'activity_level', 'daily_calories_goal']

from .models import HealthProfile

class HealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProfile
        fields = '__all__' # أو حددي الحقول اللي محتاجاها