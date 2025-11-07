from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

from .models import UserDailyUsage, UserSessionLog


@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    UserSessionLog.objects.create(user=user, login_time=timezone.now())


@receiver(user_logged_out)
def handle_user_logged_out(sender, request, user, **kwargs):
    if user is None or not user.is_authenticated:
        return

    latest_session = (
        UserSessionLog.objects.filter(user=user, logout_time__isnull=True)
        .order_by('-login_time')
        .first()
    )

    if not latest_session:
        return

    latest_session.logout_time = timezone.now()
    latest_session.update_duration(commit=False)
    latest_session.save(update_fields=['logout_time', 'duration_seconds'])
    UserDailyUsage.add_duration(user, latest_session.login_time, latest_session.logout_time)

