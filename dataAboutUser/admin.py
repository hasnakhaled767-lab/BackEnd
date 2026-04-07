from django.contrib import admin
from .models import HealthProfile, ScanHistory, Food, AnalysisResult, FoodAlternative

admin.site.register(HealthProfile)
admin.site.register(ScanHistory)
admin.site.register(Food)
admin.site.register(AnalysisResult)
admin.site.register(FoodAlternative)