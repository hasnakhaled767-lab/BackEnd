from django.db import models
from django.contrib.auth.models import User


class HealthProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # تعديل: إضافة null=True و blank=True
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    
    # الحقول الطبية برضه نخليها False كقيمة افتراضية
    has_diabetes = models.BooleanField(default=False)
    has_blood_pressure = models.BooleanField(default=False)
    has_lactose_allergy = models.BooleanField(default=False)
    # حساب الـ BMI تلقائياً
    @property
    def bmi_value(self):
        if self.height and self.weight:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return 0

    @property
    def bmi_status(self):
        bmi = self.bmi_value
        if bmi < 18.5: return "نحافة"
        elif 18.5 <= bmi < 25: return "وزن مثالي"
        elif 25 <= bmi < 30: return "زيادة في الوزن"
        else: return "سمنة"

    # حساب الـ BMR (معادلة Mifflin-St Jeor)
    @property
    def bmr_value(self):
        if self.height and self.weight and self.age:
            if self.gender.lower() in ['female', 'female', 'أنثى']:
                return round((10 * self.weight) + (6.25 * self.height) - (5 * self.age) - 161, 0)
            else:
                return round((10 * self.weight) + (6.25 * self.height) - (5 * self.age) + 5, 0)
        return 0

    def __str__(self):
        return f"Profile: {self.user.username}"
# 2. جدول الأطعمة (بيانات مرجعية للأكلات)
class Food(models.Model):
    name = models.CharField(max_length=100)
    calories = models.IntegerField(help_text="Calories per 100g")
    protein = models.FloatField(default=0.0)
    carbs = models.FloatField(default=0.0)
    fats = models.FloatField(default=0.0)
    image = models.ImageField(upload_to='foods/', null=True, blank=True) # العمود الجديد

    def __str__(self):
        return self.name

# 3. جدول سجل الفحوصات (يربط المستخدم بالأكلة وصورتها)
class ScanHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_name = models.CharField(max_length=255)
    calories = models.FloatField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fats = models.FloatField()
    is_healthy = models.BooleanField(default=True)
    image = models.ImageField(upload_to='scans/', null=True, blank=True)
    scan_date = models.DateTimeField(auto_now_add=True) # بيسجل التاريخ والوقت تلقائياً
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