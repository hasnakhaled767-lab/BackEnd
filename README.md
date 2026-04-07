 🥗 NutriGuide - Backend API

هذا المشروع هو الجزء الخاص بالخلفية (**Backend**) لتطبيق صحي يهدف إلى مساعدة المستخدمين في تتبع نظامهم الغذائي ومعرفة بدائل الأطعمة الصحية. تم بناء المشروع باستخدام إطار العمل **Django** و **Django REST Framework**.

## 🚀 المميزات (Features)
* **إدارة الأطعمة:** إضافة وعرض قائمة الأطعمة مع تفاصيلها الغذائية.
* **بدائل صحية:** توفير بدائل ذكية للأطعمة غير الصحية.
* **سجل المسح (Scan History):** تتبع عمليات البحث التي قام بها المستخدم.
* **لوحة تحكم (Admin Panel):** واجهة متكاملة لإدارة البيانات بسهولة.
* **توثيق API:** مجهز بـ **Swagger/Redoc** لتسهيل عمل فريق الـ Frontend.

## 🛠️ التقنيات المستخدمة (Tech Stack)
* **Python** (الغة الأساسية)
* **Django** (Web Framework)
* **Django REST Framework** (لبناء الـ APIs)
* **SQLite** (قاعدة البيانات الافتراضية)
* **GitHub** (لإدارة النسخ والملفات)

## 📦 كيفية التشغيل (Installation)
1. قم بتحميل المشروع (Clone):
   ```bash
   git clone https://github.com/hasnakhaled767-lab/BackEnd.git
   ```
2. إنشاء بيئة افتراضية وتفعيلها:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. تثبيت المكتبات اللازمة:
   ```bash
   pip install -r requirements.txt
   ```
4. تشغيل السيرفر:
   ```bash
   python manage.py runserver
   ```
