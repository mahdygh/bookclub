from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class MemberProfile(models.Model):
    """پروفایل عضو"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, verbose_name="شماره تلفن")
    bio = models.TextField(blank=True, verbose_name="بیوگرافی")
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name="تصویر پروفایل")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پروفایل عضو"
        verbose_name_plural = "پروفایل‌های اعضا"

    def __str__(self):
        return f"پروفایل {self.user.username}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username


class UserSessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_logs', verbose_name='کاربر')
    login_time = models.DateTimeField(verbose_name='زمان ورود')
    logout_time = models.DateTimeField(blank=True, null=True, verbose_name='زمان خروج')
    duration_seconds = models.PositiveBigIntegerField(default=0, verbose_name='مدت حضور (ثانیه)')

    class Meta:
        verbose_name = 'نشست کاربر'
        verbose_name_plural = 'نشست‌های کاربران'
        ordering = ['-login_time']

    def __str__(self):
        return f"نشست {self.user.username} در {timezone.localtime(self.login_time).strftime('%Y-%m-%d %H:%M:%S')}"

    def _current_end_time(self):
        return self.logout_time or timezone.now()

    def update_duration(self, commit=True):
        self.duration_seconds = max(int((self._current_end_time() - self.login_time).total_seconds()), 0)
        if commit:
            super().save(update_fields=['duration_seconds'])

    @property
    def session_duration_display(self):
        seconds = max(int((self._current_end_time() - self.login_time).total_seconds()), 0)
        return self._format_seconds(seconds)

    @property
    def user_total_duration_display(self):
        seconds = self.total_duration_for_user(self.user)
        return self._format_seconds(seconds)

    @classmethod
    def total_duration_for_user(cls, user):
        closed_total = cls.objects.filter(user=user, logout_time__isnull=False).aggregate(total=Sum('duration_seconds'))['total'] or 0
        open_sessions = cls.objects.filter(user=user, logout_time__isnull=True)
        now = timezone.now()
        open_total = 0
        for session in open_sessions:
            open_total += max(int((now - session.login_time).total_seconds()), 0)
        return closed_total + open_total

    @staticmethod
    def _format_seconds(total_seconds):
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if hours:
            parts.append(f"{hours} ساعت")
        if minutes:
            parts.append(f"{minutes} دقیقه")
        if not parts:
            parts.append(f"{seconds} ثانیه")
        return ' و '.join(parts)


class UserDailyUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_usages', verbose_name='کاربر')
    date = models.DateField(verbose_name='تاریخ')
    duration_seconds = models.PositiveBigIntegerField(default=0, verbose_name='مدت حضور در روز (ثانیه)')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'حضور روزانه کاربر'
        verbose_name_plural = 'حضور روزانه کاربران'
        ordering = ['-date', '-updated_at']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    @property
    def duration_display(self):
        return UserSessionLog._format_seconds(self.duration_seconds)

    @classmethod
    def add_duration(cls, user, start_dt, end_dt):
        if end_dt is None or start_dt is None or end_dt <= start_dt:
            return

        start_local = timezone.localtime(start_dt)
        end_local = timezone.localtime(end_dt)

        current_start = start_local

        while current_start.date() < end_local.date():
            day_end = current_start.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            seconds = int((day_end - current_start).total_seconds())
            cls._update_or_create_duration(user, current_start.date(), seconds)
            current_start = day_end

        remaining_seconds = int((end_local - current_start).total_seconds())
        if remaining_seconds > 0:
            cls._update_or_create_duration(user, current_start.date(), remaining_seconds)

    @classmethod
    def _update_or_create_duration(cls, user, date, seconds):
        if seconds <= 0:
            return

        obj, created = cls.objects.get_or_create(user=user, date=date, defaults={'duration_seconds': seconds})
        if not created:
            cls.objects.filter(pk=obj.pk).update(duration_seconds=F('duration_seconds') + seconds)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """ایجاد پروفایل عضو هنگام ایجاد کاربر"""
    if created:
        MemberProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """ذخیره پروفایل عضو هنگام به‌روزرسانی کاربر"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
