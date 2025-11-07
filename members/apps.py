from django.apps import AppConfig


class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'members'

    def ready(self):
        # ایمپورت سیگنال‌ها برای ثبت لاگ‌های ورود و خروج کاربران
        from . import signals  # noqa: F401
