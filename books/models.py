from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

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

class Member(models.Model):
    """عضو گروه (بدون یوزر)"""
    first_name = models.CharField(max_length=100, verbose_name="نام", null=True, blank=True)
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی", null=True, blank=True)
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
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

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
    """تخصیص کتاب به عضو"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="عضو")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    assigned_date = models.DateTimeField(verbose_name="تاریخ تخصیص")
    due_date = models.DateTimeField(verbose_name="تاریخ موعد")
    returned_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ بازگشت")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")
    reading_score_earned = models.IntegerField(default=0, verbose_name="امتیاز مطالعه کسب شده")
    quiz_score_earned = models.IntegerField(default=0, verbose_name="امتیاز آزمون کسب شده")
    late_days = models.IntegerField(default=0, verbose_name="روزهای تاخیر")
    notes = models.TextField(blank=True, verbose_name="یادداشت‌ها")

    class Meta:
        verbose_name = "تخصیص کتاب"
        verbose_name_plural = "تخصیص‌های کتاب"
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.member.full_name} - {self.book.title}"

    def save(self, *args, **kwargs):
        if not self.due_date:
            # محاسبه تاریخ موعد بر اساس تعداد روز مطالعه
            self.due_date = self.assigned_date + timedelta(days=self.book.reading_days)
        super().save(*args, **kwargs)

    def calculate_late_penalty(self):
        """محاسبه جریمه تاخیر"""
        if self.returned_date and self.returned_date > self.due_date:
            late_delta = self.returned_date - self.due_date
            self.late_days = late_delta.days
            penalty = self.late_days * 10  # 10 امتیاز برای هر روز تاخیر
            return max(0, self.book.reading_score - penalty)
        return self.book.reading_score

    def complete_assignment(self, quiz_score, notes=""):
        """تکمیل تخصیص کتاب"""
        self.returned_date = timezone.now()
        self.quiz_score_earned = quiz_score
        self.reading_score_earned = self.calculate_late_penalty()
        self.is_completed = True
        self.notes = notes
        self.save()
        
        # به‌روزرسانی امتیاز کل عضو
        self.member.total_score += self.reading_score_earned + self.quiz_score_earned
        self.member.save()
        
        # بررسی پیشرفت به مرحله بعد
        if self.member.can_advance_to_next_stage():
            self.member.advance_to_next_stage()
