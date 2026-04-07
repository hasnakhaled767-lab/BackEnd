from django.test import TestCase
from django.contrib.auth.models import User
from .models import HealthProfile, ScanHistory

class NutriScanDatabaseTest(TestCase):
    
    def setUp(self):
        # 1. إنشاء مستخدم وهمي للتجربة
        self.user = User.objects.create_user(username='testuser', password='password123')
        
    def test_create_health_profile(self):
        # 2. اختبار إنشاء ملف صحي للمستخدم
        profile = HealthProfile.objects.create(
            user=self.user,
            weight=75,
            height=180,
            chronic_diseases=["السكري"]
        )
        self.assertEqual(profile.weight, 75)
        self.assertEqual(profile.user.username, 'testuser')

    def test_create_scan_history(self):
        # 3. اختبار تسجيل فحص أكلة جديد
        scan = ScanHistory.objects.create(
            user=self.user,
            detected_food="بروكلي",
            ai_analysis="وجبة صحية جداً"
        )
        self.assertEqual(scan.detected_food, "بروكلي")
        self.assertTrue(ScanHistory.objects.filter(user=self.user).exists())