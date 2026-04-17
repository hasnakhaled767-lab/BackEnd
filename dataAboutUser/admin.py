from django.contrib import admin
from .models import HealthProfile, ScanHistory, Food, FoodAlternative

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
    list_display = ('name', 'calories', 'protein', 'carbs', 'fats', 'image')
    search_fields = ('name',)

admin.site.register(FoodAlternative)


@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    # اتأكدي إن الأسماء دي هي اللي في الموديل بالظبط
    list_display = ['user', 'food_name', 'scan_date', 'is_healthy', 'image', 'calories', 'protein', 'carbs', 'fats', 'suggested_alternative']



from django.contrib.auth.models import Group

# السطر ده هو اللي بيمسح الـ Group من قائمة الـ Admin
admin.site.unregister(Group)