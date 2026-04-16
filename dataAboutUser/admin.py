from django.contrib import admin
from .models import HealthProfile, ScanHistory, Food, AnalysisResult, FoodAlternative

@admin.register(HealthProfile)
class HealthProfileAdmin(admin.ModelAdmin):
    # شيلي 'daily_calories_goal' من هنا لو مش موجودة كحقل أساسي
    # وضيفي الـ properties اللي عملناها في الموديل عشان تظهر في جدول الأدمين
    list_display = ('user', 'height', 'weight', 'age', 'gender', 'get_bmi', 'get_bmr')

    def get_bmi(self, obj):
        return obj.bmi_value
    get_bmi.short_description = 'BMI'

    def get_bmr(self, obj):
        return obj.bmr_value
    get_bmr.short_description = 'BMR'

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'fats')
    search_fields = ('name',)

admin.site.register(ScanHistory)
admin.site.register(AnalysisResult)
admin.site.register(FoodAlternative)