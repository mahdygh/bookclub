# Generated manually due to unavailable Python runtime during development.

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSessionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('login_time', models.DateTimeField(verbose_name='زمان ورود')),
                ('logout_time', models.DateTimeField(blank=True, null=True, verbose_name='زمان خروج')),
                ('duration_seconds', models.PositiveBigIntegerField(default=0, verbose_name='مدت حضور (ثانیه)')),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name='session_logs',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='کاربر',
                    ),
                ),
            ],
            options={
                'verbose_name': 'نشست کاربر',
                'verbose_name_plural': 'نشست‌های کاربران',
                'ordering': ['-login_time'],
            },
        ),
    ]

