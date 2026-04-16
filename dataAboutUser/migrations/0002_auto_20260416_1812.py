from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('dataAboutUser', '0001_initial'), # اتأكدي إن الاسم ده صح حسب ملفاتك
    ]
    operations = [
        migrations.AlterField(
            model_name='healthprofile',
            name='height',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='healthprofile',
            name='weight',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='healthprofile',
            name='age',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]