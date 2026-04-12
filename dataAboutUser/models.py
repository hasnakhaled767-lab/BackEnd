from django.db import models
from django.contrib.auth.models import User

class HealthProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], null=True)
    daily_calories_goal = models.IntegerField(null=True, blank=True)
    
    has_diabetes = models.BooleanField(default=False, verbose_name="سكر")
    has_blood_pressure = models.BooleanField(default=False, verbose_name="ضغط")
    chronic_diseases = models.TextField(null=True, blank=True, verbose_name="أمراض مزمنة أخرى")
    food_allergies = models.TextField(null=True, blank=True, verbose_name="حساسية طعام")

    def __str__(self):
        return f"Health Profile for {self.user.username}"
    
# 2. جدول الأطعمة (بيانات مرجعية للأكلات)
class Food(models.Model):
    name = models.CharField(max_length=100)
    calories = models.IntegerField(help_text="Calories per 100g")
    protein = models.FloatField(default=0.0)
    carbs = models.FloatField(default=0.0)
    fats = models.FloatField(default=0.0)

    def __str__(self):
        return self.name

# 3. جدول سجل الفحوصات (يربط المستخدم بالأكلة وصورتها)
class ScanHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.SET_NULL, null=True, blank=True)
    detected_food_name = models.CharField(max_length=100, null=True, blank=True) 
    image = models.ImageField(upload_to='scans/', null=True, blank=True) # يحتاج مكتبة Pillow
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} scanned {self.detected_food_name}"

# 4. جدول نتائج التحليل (فصل تفاصيل التحليل عن السجل العام)
class AnalysisResult(models.Model):
    scan = models.OneToOneField(ScanHistory, on_delete=models.CASCADE)
    ai_feedback = models.TextField()
    health_score = models.IntegerField(null=True, blank=True)
    is_safe = models.BooleanField(default=True)

# 5. جدول البدائل الصحية (يربط الأكلة ببديل أفضل منها)
class FoodAlternative(models.Model):
    original_food = models.ForeignKey(Food, related_name='alternatives', on_delete=models.CASCADE)
    suggested_alternative = models.ForeignKey(Food, related_name='substitutes', on_delete=models.CASCADE)
    reason_why = models.TextField()

    def __str__(self):
        return f"Alternative for {self.original_food.name}"