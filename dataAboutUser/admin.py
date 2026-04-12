from django.contrib import admin
from .models import HealthProfile, ScanHistory, Food, AnalysisResult, FoodAlternative

@admin.register(HealthProfile)
class HealthProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'has_diabetes', 'has_blood_pressure', 'daily_calories_goal')
    search_fields = ('user__username',)
    list_filter = ('has_diabetes', 'has_blood_pressure', 'gender')

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'fats')
    search_fields = ('name',)

admin.site.register(ScanHistory)
admin.site.register(AnalysisResult)
admin.site.register(FoodAlternative)