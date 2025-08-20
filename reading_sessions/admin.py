from django.contrib import admin
from .models import BookHandout, BookReturn, Quiz, QuizQuestion, QuizChoice, QuizAttempt


@admin.register(BookHandout)
class BookHandoutAdmin(admin.ModelAdmin):
    list_display = ['book', 'member', 'handed_out_date', 'due_date']
    list_filter = ['handed_out_date', 'due_date']
    search_fields = ['book__title', 'member__user__username']
    ordering = ['-handed_out_date']


@admin.register(BookReturn)
class BookReturnAdmin(admin.ModelAdmin):
    list_display = ['handout', 'returned_date', 'quiz_score', 'total_score', 'late_days']
    list_filter = ['returned_date', 'late_days']
    search_fields = ['handout__book__title', 'handout__member__user__username']
    ordering = ['-returned_date']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['book', 'title', 'max_score', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['book__title', 'title']
    ordering = ['-created_at']


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'question_text', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'quiz']
    search_fields = ['question_text']
    ordering = ['quiz', 'order']


@admin.register(QuizChoice)
class QuizChoiceAdmin(admin.ModelAdmin):
    list_display = ['question', 'choice_text', 'is_correct']
    list_filter = ['is_correct', 'question__quiz']
    search_fields = ['choice_text', 'question__question_text']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'member', 'started_at', 'completed_at', 'score', 'is_completed']
    list_filter = ['is_completed', 'started_at', 'completed_at']
    search_fields = ['quiz__title', 'member__user__username']
    ordering = ['-started_at']
