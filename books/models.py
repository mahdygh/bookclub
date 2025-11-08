from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

class ReadingPeriod(models.Model):
    """دوره کتابخوانی"""
    name = models.CharField(max_length=200, verbose_name="نام دوره")
    description = models.TextField(verbose_name="توضیحات")
    is_active = models.BooleanField(default=False, verbose_name="فعال")
    start_date = models.DateField(verbose_name="تاریخ شروع")
    end_date = models.DateField(verbose_name="تاریخ پایان")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "دوره کتابخوانی"
        verbose_name_plural = "دوره‌های کتابخوانی"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_active:
            # فقط یک دوره فعال می‌تواند وجود داشته باشد
            ReadingPeriod.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("تاریخ شروع باید قبل از تاریخ پایان باشد")

class Stage(models.Model):
    """مرحله دوره"""
    period = models.ForeignKey(ReadingPeriod, on_delete=models.CASCADE, verbose_name="دوره")
    stage_number = models.IntegerField(verbose_name="شماره مرحله")
    name = models.CharField(max_length=100, verbose_name="نام مرحله")
    description = models.TextField(verbose_name="توضیحات")
    image = models.ImageField(upload_to='stages/images/', blank=True, null=True, verbose_name="تصویر مرحله")
    order = models.IntegerField(verbose_name="ترتیب")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مرحله"
        verbose_name_plural = "مراحل"
        unique_together = ['period', 'stage_number']
        ordering = ['order', 'stage_number']

    def __str__(self):
        return f"{self.period.name} - {self.name}"

class Book(models.Model):
    """کتاب"""
    title = models.CharField(max_length=200, verbose_name="عنوان کتاب")
    author = models.CharField(max_length=200, verbose_name="نویسنده")
    description = models.TextField(verbose_name="توضیحات")
    cover_image = models.ImageField(upload_to='books/covers/', blank=True, null=True, verbose_name="تصویر جلد")
    reading_score = models.IntegerField(default=0, verbose_name="امتیاز مطالعه")
    quiz_score = models.IntegerField(default=0, verbose_name="امتیاز آزمون")
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, verbose_name="مرحله")
    reading_days = models.IntegerField(default=3, verbose_name="تعداد روز مطالعه")
    page_count = models.PositiveIntegerField(default=0, verbose_name="تعداد صفحات")
    stock_count = models.PositiveIntegerField(default=1, verbose_name="تعداد نسخه")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "کتاب"
        verbose_name_plural = "کتاب‌ها"
        ordering = ['stage__order', 'title']

    def __str__(self):
        return self.title

    @property
    def total_score(self):
        """مجموع امتیازات"""
        return self.reading_score + self.quiz_score

    def save(self, *args, **kwargs):
        old_reading = None
        old_quiz = None
        if self.pk:
            try:
                old_self = Book.objects.get(pk=self.pk)
                old_reading = old_self.reading_score
                old_quiz = old_self.quiz_score
            except Book.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if self.pk and old_reading is not None:
            reading_changed = old_reading != self.reading_score
            quiz_changed = old_quiz != self.quiz_score
            if reading_changed or quiz_changed:
                for assignment in self.bookassignment_set.filter(is_completed=True).select_related('member'):
                    assignment.apply_book_score_change(self.reading_score, self.quiz_score)

class Member(models.Model):
    """عضو گروه"""
    GROUP_CHOICES = [
        ('soleimani', 'گروه شهید سلیمانی'),
        ('fakhrizadeh', 'گروه شهید فخری زاده'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="کاربر")
    first_name = models.CharField(max_length=100, verbose_name="نام", null=True, blank=True)
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی", null=True, blank=True)
    group = models.CharField(max_length=20, choices=GROUP_CHOICES, default='fakhrizadeh', verbose_name="گروه")
    profile_image = models.ImageField(upload_to='members/profiles/', blank=True, null=True, verbose_name="تصویر پروفایل")
    current_stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="مرحله فعلی")
    total_score = models.IntegerField(default=0, verbose_name="امتیاز کل")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "عضو"
        verbose_name_plural = "اعضا"
        ordering = ['-total_score', 'first_name']

    def __str__(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}" if self.user.first_name else self.user.username
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}" if self.user.first_name else self.user.username
        return f"{self.first_name} {self.last_name}"
    
    def has_user_account(self):
        """آیا عضو حساب کاربری دارد؟"""
        return self.user is not None
    
    def create_user_account(self, username, password, email=None):
        """ایجاد حساب کاربری برای عضو"""
        if self.user:
            return False, "این عضو قبلاً حساب کاربری دارد"
        
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email or '',
                first_name=self.first_name or '',
                last_name=self.last_name or ''
            )
            self.user = user
            self.save()
            return True, "حساب کاربری با موفقیت ایجاد شد"
        except Exception as e:
            return False, f"خطا در ایجاد حساب کاربری: {str(e)}"
    
    def update_user_info(self, first_name=None, last_name=None, email=None):
        """به‌روزرسانی اطلاعات کاربر"""
        if not self.user:
            return False, "این عضو حساب کاربری ندارد"
        
        try:
            if first_name is not None:
                self.user.first_name = first_name
                self.first_name = first_name
            if last_name is not None:
                self.user.last_name = last_name
                self.last_name = last_name
            if email is not None:
                self.user.email = email
            
            self.user.save()
            self.save()
            return True, "اطلاعات با موفقیت به‌روزرسانی شد"
        except Exception as e:
            return False, f"خطا در به‌روزرسانی: {str(e)}"

    def get_current_stage_books(self):
        """کتاب‌های مرحله فعلی"""
        if self.current_stage:
            return Book.objects.filter(stage=self.current_stage)
        return Book.objects.none()

    def get_completed_books_count(self):
        """تعداد کتاب‌های تکمیل شده در مرحله فعلی"""
        if self.current_stage:
            return BookAssignment.objects.filter(
                member=self,
                book__stage=self.current_stage,
                is_completed=True
            ).count()
        return 0

    def get_total_books_in_stage(self):
        """تعداد کل کتاب‌های مرحله فعلی"""
        if self.current_stage:
            return Book.objects.filter(stage=self.current_stage).count()
        return 0

    def get_stage_progress_percentage(self):
        """درصد پیشرفت در مرحله فعلی"""
        total = self.get_total_books_in_stage()
        if total > 0:
            completed = self.get_completed_books_count()
            return round((completed / total) * 100, 1)
        return 0

    def can_advance_to_next_stage(self):
        """آیا می‌تواند به مرحله بعد برود؟"""
        if not self.current_stage:
            return False
        
        total_books = self.get_total_books_in_stage()
        completed_books = self.get_completed_books_count()
        
        return completed_books >= total_books

    def advance_to_next_stage(self):
        """پیشرفت به مرحله بعد"""
        if not self.can_advance_to_next_stage():
            return False
        
        next_stage = Stage.objects.filter(
            period=self.current_stage.period,
            order__gt=self.current_stage.order
        ).order_by('order').first()
        
        if next_stage:
            self.current_stage = next_stage
            self.save()
            return True
        return False

class BookAssignment(models.Model):
    """امانت گرفتن کتاب توسط عضو"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="عضو")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    assigned_date = models.DateTimeField(verbose_name="تاریخ امانت گرفتن")
    due_date = models.DateTimeField(verbose_name="تاریخ موعد")
    returned_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ بازگشت")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")
    reading_score_earned = models.IntegerField(default=0, verbose_name="امتیاز مطالعه کسب شده")
    quiz_score_earned = models.IntegerField(default=0, verbose_name="امتیاز آزمون کسب شده")
    late_days = models.IntegerField(default=0, verbose_name="روزهای تاخیر")
    pages_read = models.PositiveIntegerField(default=0, verbose_name="تعداد صفحات مطالعه شده")
    reading_score_base = models.IntegerField(default=0, verbose_name="امتیاز مطالعه پایه")
    quiz_score_base = models.IntegerField(default=0, verbose_name="امتیاز آزمون پایه")
    notes = models.TextField(blank=True, verbose_name="یادداشت‌ها")

    class Meta:
        verbose_name = "امانت گرفتن کتاب"
        verbose_name_plural = "امانت‌های کتاب"
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.member.full_name} - {self.book.title}"

    @property
    def total_score(self):
        reading = self.reading_score_earned or 0
        quiz = self.quiz_score_earned or 0
        return max(reading, 0) + max(quiz, 0)

    @property
    def penalty_amount(self):
        base_score = self.reading_score_base
        if not base_score and base_score != 0:
            base_score = self.book.reading_score if self.book else 0
        base_score = max(base_score or 0, 0)
        earned_score = max(self.reading_score_earned or 0, 0)

        if self.is_completed:
            return max(base_score - earned_score, 0)

        late_days = max(self.late_days or 0, 0)
        if late_days > 0:
            return min(base_score, late_days * 2)

        return 0

    def normalize_completion_state(self):
        if not self.returned_date:
            return False

        changed_fields = set()

        if not self.is_completed:
            self.is_completed = True
            changed_fields.add('is_completed')

        if self.book:
            if not self.reading_score_base:
                self.reading_score_base = self.book.reading_score
                changed_fields.add('reading_score_base')
            if not self.quiz_score_base:
                self.quiz_score_base = self.book.quiz_score
                changed_fields.add('quiz_score_base')
            if not self.quiz_score_earned:
                self.quiz_score_earned = self.book.quiz_score
                changed_fields.add('quiz_score_earned')
            if not self.pages_read:
                self.pages_read = self.book.page_count or 0
                changed_fields.add('pages_read')

        recalculated_reading = self.calculate_late_penalty()
        if self.reading_score_earned != recalculated_reading:
            self.reading_score_earned = recalculated_reading
            changed_fields.update({'reading_score_earned', 'late_days'})

        if not changed_fields:
            return False

        changed_fields.add('returned_date')
        self.save(update_fields=list(changed_fields))
        return True

    @classmethod
    def normalize_all_returned(cls):
        pending_qs = cls.objects.filter(returned_date__isnull=False, is_completed=False)
        for assignment in pending_qs.select_related('book', 'member'):
            assignment.normalize_completion_state()

    def save(self, *args, **kwargs):
        previous_instance = None
        if self.pk:
            try:
                previous_instance = BookAssignment.objects.select_related('member').get(pk=self.pk)
            except BookAssignment.DoesNotExist:
                previous_instance = None

        if self.returned_date and timezone.is_naive(self.returned_date):
            self.returned_date = timezone.make_aware(self.returned_date, timezone.get_current_timezone())

        if not self.due_date:
            self.due_date = self.assigned_date + timedelta(days=self.book.reading_days)
        elif timezone.is_naive(self.due_date):
            self.due_date = timezone.make_aware(self.due_date, timezone.get_current_timezone())

        auto_completed = False
        if self.returned_date and not self.is_completed:
            self.is_completed = True
            auto_completed = True

        if self.book:
            if self.is_completed:
                if self.reading_score_base in (None, 0):
                    self.reading_score_base = self.book.reading_score
                if self.quiz_score_base in (None, 0):
                    self.quiz_score_base = self.book.quiz_score
                if self.quiz_score_earned in (None, 0):
                    self.quiz_score_earned = self.book.quiz_score
                if self.pages_read in (None, 0):
                    self.pages_read = self.book.page_count or 0

                if auto_completed or self.reading_score_earned is None:
                    self.reading_score_earned = self.calculate_late_penalty()
                elif self.returned_date and (self.late_days is None or self.late_days < 0):
                    self.calculate_late_penalty()
            else:
                if self.pages_read is None:
                    self.pages_read = 0
                self.late_days = self.late_days or 0

        super().save(*args, **kwargs)
        self.sync_member_scores(previous_instance)

    def calculate_late_penalty(self):
        """محاسبه جریمه تاخیر"""
        if self.returned_date and self.due_date:
            returned_dt = timezone.localtime(self.returned_date) if timezone.is_aware(self.returned_date) else self.returned_date
            due_dt = timezone.localtime(self.due_date) if timezone.is_aware(self.due_date) else self.due_date
            if returned_dt > due_dt:
                late_delta = returned_dt - due_dt
                self.late_days = max(late_delta.days, 0)
                penalty = self.late_days * 2
                return max(0, self.book.reading_score - penalty)
        self.late_days = 0
        return self.book.reading_score

    def complete_assignment(self, quiz_score, notes=""):
        """تکمیل امانت گرفتن کتاب"""
        self.returned_date = timezone.now()
        if self.book:
            self.reading_score_base = self.book.reading_score
            self.quiz_score_base = self.book.quiz_score
        else:
            self.reading_score_base = self.reading_score_base or 0
            self.quiz_score_base = self.quiz_score_base or 0
        self.quiz_score_earned = quiz_score
        self.reading_score_earned = self.calculate_late_penalty()
        self.pages_read = self.book.page_count if self.book and self.book.page_count else 0
        self.is_completed = True
        self.notes = notes
        self.save()
        
        # به‌روزرسانی امتیاز کل عضو
        earned_score = self.reading_score_earned + self.quiz_score_earned
        self.member.total_score += earned_score
        self.member.save()
        
        # به‌روزرسانی امتیاز هفتگی
        from datetime import date, timedelta
        today = date.today()
        # محاسبه شروع هفته (شنبه)
        days_since_saturday = (today.weekday() + 2) % 7
        week_start = today - timedelta(days=days_since_saturday)
        week_end = week_start + timedelta(days=6)
        
        weekly_score, created = WeeklyScore.objects.get_or_create(
            member=self.member,
            week_start_date=week_start,
            defaults={'week_end_date': week_end, 'weekly_score': 0}
        )
        weekly_score.weekly_score += earned_score
        weekly_score.save()
        
        # بررسی پیشرفت به مرحله بعد
        if self.member.can_advance_to_next_stage():
            self.member.advance_to_next_stage()

    @staticmethod
    def _week_bounds(reference_datetime):
        if not reference_datetime:
            return None, None
        if timezone.is_aware(reference_datetime):
            local_dt = timezone.localtime(reference_datetime)
        else:
            local_dt = timezone.make_aware(reference_datetime, timezone.get_current_timezone())
        base_date = local_dt.date()
        days_since_saturday = (base_date.weekday() + 2) % 7
        week_start = base_date - timedelta(days=days_since_saturday)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    @staticmethod
    def _apply_score_delta_to_member(member, delta, reference_datetime):
        if not member or delta == 0:
            return

        member.total_score = max(member.total_score + delta, 0)
        member.save(update_fields=['total_score'])

        if not reference_datetime:
            return

        week_start, week_end = BookAssignment._week_bounds(reference_datetime)
        if not week_start:
            return

        weekly_defaults = {'week_end_date': week_end, 'weekly_score': 0}
        weekly, created = WeeklyScore.objects.get_or_create(
            member=member,
            week_start_date=week_start,
            defaults=weekly_defaults,
        )
        if delta < 0 and created:
            return

        weekly.week_end_date = week_end
        weekly.weekly_score = max(weekly.weekly_score + delta, 0)
        weekly.save(update_fields=['week_end_date', 'weekly_score'])

    def apply_score_delta(self, delta, reference_datetime=None):
        if delta == 0:
            return
        reference = reference_datetime or self.returned_date
        self._apply_score_delta_to_member(self.member, delta, reference)

    def sync_member_scores(self, previous_instance=None):
        prev_member = previous_instance.member if previous_instance else None
        prev_total = previous_instance.total_score if previous_instance and previous_instance.is_completed else 0
        prev_reference = previous_instance.returned_date if previous_instance and previous_instance.is_completed else None

        current_total = self.total_score if self.is_completed else 0
        current_reference = self.returned_date or prev_reference

        if prev_member == self.member:
            delta = current_total - prev_total
            self.apply_score_delta(delta, current_reference)
        else:
            if prev_member:
                self._apply_score_delta_to_member(prev_member, -prev_total, prev_reference)
            self.apply_score_delta(current_total, current_reference)

    def apply_book_score_change(self, new_reading_base, new_quiz_base):
        if not self.is_completed:
            return

        old_total = self.total_score

        old_reading_base = self.reading_score_base or (self.book.reading_score if self.book else 0)
        old_reading_earned = self.reading_score_earned or 0
        penalty_amount = max(old_reading_base - old_reading_earned, 0)
        new_reading_base = max(new_reading_base or 0, 0)
        new_reading_earned = max(new_reading_base - penalty_amount, 0)

        old_quiz_base = self.quiz_score_base or (self.quiz_score_earned or (self.book.quiz_score if self.book else 0))
        old_quiz_earned = self.quiz_score_earned or 0
        new_quiz_base = max(new_quiz_base or 0, 0)
        if old_quiz_base > 0:
            ratio = old_quiz_earned / old_quiz_base
            new_quiz_earned = round(ratio * new_quiz_base)
        else:
            new_quiz_earned = min(old_quiz_earned, new_quiz_base)

        self.reading_score_base = new_reading_base
        self.quiz_score_base = new_quiz_base
        self.reading_score_earned = new_reading_earned
        self.quiz_score_earned = new_quiz_earned
        if self.book and self.book.page_count:
            self.pages_read = self.book.page_count

        self.save(update_fields=['reading_score_base', 'quiz_score_base', 'reading_score_earned', 'quiz_score_earned', 'pages_read'])

        new_total = self.total_score
        delta = new_total - old_total
        self.apply_score_delta(delta, self.returned_date)

    def _adjust_member_on_delete(self):
        if not self.is_completed:
            return

        total = (self.reading_score_earned or 0) + (self.quiz_score_earned or 0)
        reference = self.returned_date
        self._apply_score_delta_to_member(self.member, -total, reference)

class WeeklyScore(models.Model):
    """امتیاز هفتگی اعضا"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="عضو", related_name='weekly_scores')
    week_start_date = models.DateField(verbose_name="تاریخ شروع هفته")
    week_end_date = models.DateField(verbose_name="تاریخ پایان هفته")
    weekly_score = models.IntegerField(default=0, verbose_name="امتیاز هفتگی")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "امتیاز هفتگی"
        verbose_name_plural = "امتیازات هفتگی"
        ordering = ['-weekly_score', '-week_start_date']
        unique_together = ['member', 'week_start_date']

    def __str__(self):
        return f"{self.member.full_name} - هفته {self.week_start_date}"


class Notification(models.Model):
    TYPE_GENERAL = 'general'
    TYPE_PRIVATE = 'private'
    TYPE_DUE = 'due_reminder'

    TYPE_CHOICES = [
        (TYPE_GENERAL, 'اعلان عمومی'),
        (TYPE_PRIVATE, 'اعلان خصوصی'),
        (TYPE_DUE, 'یادآوری موعد'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications', verbose_name='گیرنده')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    message = models.TextField(verbose_name='متن پیام')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_GENERAL, verbose_name='نوع اعلان')
    related_assignment = models.ForeignKey('BookAssignment', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications', verbose_name='امانت مرتبط')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications', verbose_name='ایجادکننده')
    is_read = models.BooleanField(default=False, verbose_name='خوانده شده؟')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')

    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


@receiver(pre_delete, sender=BookAssignment)
def handle_bookassignment_pre_delete(sender, instance, **kwargs):
    instance._adjust_member_on_delete()
