from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
