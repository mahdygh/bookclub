from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
import jdatetime
from .models import ReadingPeriod, Stage, Book, Member, BookAssignment, WeeklyScore

class ReadingPeriodAdminForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="تاریخ شروع (شمسی)",
        help_text="تاریخ را به صورت شمسی وارد کنید"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="تاریخ پایان (شمسی)",
        help_text="تاریخ را به صورت شمسی وارد کنید"
    )
    
    class Meta:
        model = ReadingPeriod
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("تاریخ شروع باید قبل از تاریخ پایان باشد")
        
        return cleaned_data

@admin.register(ReadingPeriod)
class ReadingPeriodAdmin(admin.ModelAdmin):
    form = ReadingPeriodAdminForm
    list_display = ['name', 'is_active', 'start_date_jalali', 'end_date_jalali', 'created_at_jalali']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('stage_set')
    
    def start_date_jalali(self, obj):
        if obj.start_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.start_date).strftime('%Y/%m/%d')
        return '-'
    start_date_jalali.short_description = "تاریخ شروع (شمسی)"
    
    def end_date_jalali(self, obj):
        if obj.end_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.end_date).strftime('%Y/%m/%d')
        return '-'
    end_date_jalali.short_description = "تاریخ پایان (شمسی)"
    
    def created_at_jalali(self, obj):
        if obj.created_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    created_at_jalali.short_description = "تاریخ ایجاد (شمسی)"

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ['name', 'period', 'stage_number', 'order', 'image_preview', 'books_count']
    list_filter = ['period', 'stage_number']
    search_fields = ['name', 'description']
    ordering = ['period', 'order', 'stage_number']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.image.url)
        return "بدون عکس"
    image_preview.short_description = "تصویر"
    
    def books_count(self, obj):
        return obj.book_set.count()
    books_count.short_description = "تعداد کتاب‌ها"

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'stage', 'reading_score', 'quiz_score', 'total_score', 'reading_days']
    list_filter = ['stage', 'reading_score', 'quiz_score']
    search_fields = ['title', 'author', 'description']
    ordering = ['stage__order', 'title']
    
    def total_score(self, obj):
        return obj.total_score
    total_score.short_description = "امتیاز کل"

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'group_display', 'current_stage', 'total_score', 'stage_progress', 'is_active']
    list_filter = ['group', 'current_stage', 'is_active', 'current_stage__period']
    search_fields = ['first_name', 'last_name']
    ordering = ['-total_score', 'first_name']
    readonly_fields = ['total_score', 'stage_progress']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "نام کامل"
    
    def group_display(self, obj):
        return obj.get_group_display()
    group_display.short_description = "گروه"
    
    def stage_progress(self, obj):
        if obj.current_stage:
            completed = obj.get_completed_books_count()
            total = obj.get_total_books_in_stage()
            percentage = obj.get_stage_progress_percentage()
            return f"{completed}/{total} ({percentage}%)"
        return "مرحله تعیین نشده"
    stage_progress.short_description = "پیشرفت مرحله"

class BookAssignmentAdminForm(forms.ModelForm):
    assigned_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="تاریخ امانت گرفتن (شمسی)",
        help_text="تاریخ و زمان امانت گرفتن را به صورت شمسی وارد کنید"
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="تاریخ موعد (شمسی)",
        help_text="تاریخ موعد را به صورت شمسی وارد کنید"
    )
    returned_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="تاریخ بازگشت (شمسی)",
        help_text="تاریخ و زمان بازگشت را به صورت شمسی وارد کنید",
        required=False
    )
    
    class Meta:
        model = BookAssignment
        fields = '__all__'

@admin.register(BookAssignment)
class BookAssignmentAdmin(admin.ModelAdmin):
    form = BookAssignmentAdminForm
    list_display = ['member', 'book', 'assigned_date_jalali', 'due_date_jalali', 'status', 'scores']
    list_filter = ['is_completed', 'assigned_date', 'due_date', 'book__stage']
    search_fields = ['member__first_name', 'member__last_name', 'book__title']
    ordering = ['-assigned_date']
    readonly_fields = ['late_days', 'reading_score_earned']
    
    fieldsets = (
        ('اطلاعات امانت گرفتن', {
            'fields': ('member', 'book', 'assigned_date', 'due_date')
        }),
        ('اطلاعات بازگشت', {
            'fields': ('returned_date', 'quiz_score_earned', 'notes')
        }),
        ('محاسبات', {
            'fields': ('is_completed', 'late_days', 'reading_score_earned'),
            'classes': ('collapse',)
        }),
    )
    
    def assigned_date_jalali(self, obj):
        if obj.assigned_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.assigned_date).strftime('%Y/%m/%d %H:%M')
        return '-'
    assigned_date_jalali.short_description = "تاریخ امانت گرفتن (شمسی)"
    
    def due_date_jalali(self, obj):
        if obj.due_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.due_date).strftime('%Y/%m/%d')
        return '-'
    due_date_jalali.short_description = "تاریخ موعد (شمسی)"
    
    def status(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green;">✓ تکمیل شده</span>')
        elif obj.due_date < obj.assigned_date.replace(tzinfo=obj.assigned_date.tzinfo):
            return format_html('<span style="color: red;">⚠ دیر شده</span>')
        else:
            return format_html('<span style="color: orange;">📖 در حال مطالعه</span>')
    status.short_description = "وضعیت"
    
    def scores(self, obj):
        if obj.is_completed:
            return f"مطالعه: {obj.reading_score_earned} | آزمون: {obj.quiz_score_earned}"
        return "-"
    scores.short_description = "امتیازات"
    
    def save_model(self, request, obj, form, change):
        # اگر کتاب بازگشت داده شده، امانت گرفتن را تکمیل کن
        if obj.returned_date and not obj.is_completed:
            obj.complete_assignment(obj.quiz_score_earned, obj.notes)
        super().save_model(request, obj, form, change)

@admin.register(WeeklyScore)
class WeeklyScoreAdmin(admin.ModelAdmin):
    list_display = ['member', 'week_start_date_jalali', 'week_end_date_jalali', 'weekly_score', 'updated_at_jalali']
    list_filter = ['week_start_date', 'member__group']
    search_fields = ['member__first_name', 'member__last_name']
    ordering = ['-week_start_date', '-weekly_score']
    readonly_fields = ['created_at', 'updated_at']
    
    def week_start_date_jalali(self, obj):
        if obj.week_start_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.week_start_date).strftime('%Y/%m/%d')
        return '-'
    week_start_date_jalali.short_description = "شروع هفته (شمسی)"
    
    def week_end_date_jalali(self, obj):
        if obj.week_end_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.week_end_date).strftime('%Y/%m/%d')
        return '-'
    week_end_date_jalali.short_description = "پایان هفته (شمسی)"
    
    def updated_at_jalali(self, obj):
        if obj.updated_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    updated_at_jalali.short_description = "آخرین به‌روزرسانی (شمسی)"
