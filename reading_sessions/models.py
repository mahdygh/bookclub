from django.db import models
from django.contrib.auth.models import User
from books.models import Book, Member, BookAssignment
from django.core.validators import MinValueValidator, MaxValueValidator


class BookHandout(models.Model):
    """تحویل کتاب به عضو"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="عضو")
    handed_out_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ تحویل")
    due_date = models.DateTimeField(verbose_name="تاریخ موعد")
    notes = models.TextField(blank=True, verbose_name="یادداشت‌ها")
    
    class Meta:
        verbose_name = "تحویل کتاب"
        verbose_name_plural = "تحویل‌های کتاب"
        ordering = ['-handed_out_date']

    def __str__(self):
        return f"{self.book.title} - {self.member}"

    def save(self, *args, **kwargs):
        if not self.due_date:
            from datetime import timedelta
            self.due_date = self.handed_out_date + timedelta(days=self.book.reading_days)
        super().save(*args, **kwargs)


class BookReturn(models.Model):
    """تحویل گرفتن کتاب از عضو"""
    handout = models.OneToOneField(BookHandout, on_delete=models.CASCADE, verbose_name="تحویل")
    returned_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ بازگشت")
    quiz_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="امتیاز آزمون"
    )
    late_days = models.IntegerField(default=0, verbose_name="روزهای تاخیر")
    final_reading_score = models.IntegerField(default=0, verbose_name="امتیاز نهایی خواندن")
    total_score = models.IntegerField(default=0, verbose_name="امتیاز کل")
    notes = models.TextField(blank=True, verbose_name="یادداشت‌ها")
    
    class Meta:
        verbose_name = "بازگشت کتاب"
        verbose_name_plural = "بازگشت‌های کتاب"
        ordering = ['-returned_date']

    def __str__(self):
        return f"بازگشت {self.handout.book.title} - {self.handout.member}"

    def save(self, *args, **kwargs):
        # محاسبه روزهای تاخیر
        if self.returned_date > self.handout.due_date:
            from datetime import timedelta
            self.late_days = (self.returned_date - self.handout.due_date).days
        else:
            self.late_days = 0
        
        # محاسبه امتیاز نهایی خواندن (کسر جریمه تاخیر)
        penalty = self.late_days * 10
        self.final_reading_score = max(0, self.handout.book.reading_score - penalty)
        
        # محاسبه امتیاز کل
        self.total_score = self.final_reading_score + self.quiz_score
        
        super().save(*args, **kwargs)
        
        # به‌روزرسانی امتیاز کل عضو
        self.handout.member.total_score += self.total_score
        self.handout.member.save()


class Quiz(models.Model):
    """آزمون کتاب"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    title = models.CharField(max_length=200, verbose_name="عنوان آزمون")
    description = models.TextField(verbose_name="توضیحات")
    max_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="حداکثر امتیاز"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "آزمون"
        verbose_name_plural = "آزمون‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.book.title} - {self.title}"


class QuizQuestion(models.Model):
    """سوال آزمون"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name="آزمون")
    question_text = models.TextField(verbose_name="متن سوال")
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('multiple_choice', 'چند گزینه‌ای'),
            ('true_false', 'درست/غلط'),
            ('short_answer', 'پاسخ کوتاه'),
        ],
        verbose_name="نوع سوال"
    )
    points = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="امتیاز"
    )
    order = models.IntegerField(verbose_name="ترتیب")
    
    class Meta:
        verbose_name = "سوال آزمون"
        verbose_name_plural = "سوالات آزمون"
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - سوال {self.order}"


class QuizChoice(models.Model):
    """گزینه سوال چند گزینه‌ای"""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='choices', verbose_name="سوال")
    choice_text = models.CharField(max_length=200, verbose_name="متن گزینه")
    is_correct = models.BooleanField(default=False, verbose_name="پاسخ صحیح")
    
    class Meta:
        verbose_name = "گزینه سوال"
        verbose_name_plural = "گزینه‌های سوال"

    def __str__(self):
        return f"{self.question} - {self.choice_text}"


class QuizAttempt(models.Model):
    """تلاش آزمون"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name="آزمون")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="عضو")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تکمیل")
    score = models.IntegerField(default=0, verbose_name="امتیاز کسب شده")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")
    
    class Meta:
        verbose_name = "تلاش آزمون"
        verbose_name_plural = "تلاش‌های آزمون"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.member} - {self.quiz}"

    def calculate_score(self):
        """محاسبه امتیاز آزمون"""
        total_points = sum(question.points for question in self.quiz.questions.all())
        if total_points > 0:
            self.score = int((self.score / total_points) * self.quiz.max_score)
        return self.score
