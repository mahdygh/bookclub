from datetime import timedelta

from django.utils import timezone
from django.db.models import Q

from .models import Notification, BookAssignment, Member


def notifications(request):
    if not request.user.is_authenticated:
        return {
            'header_notifications': [],
            'header_unread_notifications': 0,
        }

    user = request.user
    member = Member.objects.filter(user=user, is_active=True).first()
    if member:
        _ensure_due_notifications(user, member)

    notif_qs = Notification.objects.filter(
        Q(recipient=user) | Q(recipient__isnull=True)
    ).order_by('is_read', '-created_at')

    notifications_list = list(notif_qs[:5])
    unread_count = notif_qs.filter(is_read=False, recipient=user).count()

    return {
        'header_notifications': notifications_list,
        'header_unread_notifications': unread_count,
    }


def _ensure_due_notifications(user, member):
    now = timezone.now()
    reminder_date = (now + timedelta(days=2)).date()

    assignments = BookAssignment.objects.filter(
        member=member,
        is_completed=False,
        due_date__date=reminder_date
    ).select_related('book')

    for assignment in assignments:
        Notification.objects.get_or_create(
            recipient=user,
            related_assignment=assignment,
            notification_type=Notification.TYPE_DUE,
            defaults={
                'title': 'یادآوری موعد مطالعه',
                'message': (
                    f"{member.full_name} عزیز!\n"
                    f"مهلت مطالعه کتاب «{assignment.book.title}» دو روز دیگر به پایان می‌رسد.\n"
                    "به ازای هر روز تاخیر، ۲ امتیاز از شما کسر خواهد شد.\n"
                    "از طرف: مدیریت کتابخانه"
                ),
                'created_by': None,
            }
        )


