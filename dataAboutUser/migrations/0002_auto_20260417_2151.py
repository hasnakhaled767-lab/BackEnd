from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('dataAboutUser', '0001_initial'), # اتأكدي إن ده اسم آخر ملف عندك في فولدر الـ migrations
    ]

    operations = [
        migrations.AddField(
            model_name='scanhistory',
            name='food_name',
            field=models.CharField(max_length=255, default='Unknown'),
            preserve_default=False,
        ),
    ]