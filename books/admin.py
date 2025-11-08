from datetime import date, timedelta

import jdatetime
from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.db.models import Count

from .models import ReadingPeriod, Stage, Book, Member, BookAssignment, WeeklyScore, Notification

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
    list_display = ['title', 'author', 'stage', 'page_count', 'stock_count', 'reading_score', 'quiz_score', 'total_score', 'reading_days']
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
    readonly_fields = ['stage_progress']
    
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
        help_text="تاریخ و زمان امانت گرفتن را به صورت شمسی وارد کنید",
        required=False
    )
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="تاریخ موعد (شمسی)",
        help_text="تاریخ موعد باتوجه به مهلت کتاب به صورت خودکار محاسبه می‌شود",
        required=False
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        book_field = self.fields.get('book')
        if book_field:
            selected_member_id = None
            if self.instance.pk and self.instance.member_id:
                selected_member_id = self.instance.member_id
            else:
                prefixed_member_key = self.add_prefix('member')
                candidate = self.data.get(prefixed_member_key) or self.data.get('member')
                if not candidate:
                    candidate = self.initial.get('member')
                selected_member_id = candidate

            book_field.queryset = Book.objects.none()

            member = None
            if selected_member_id:
                try:
                    member = Member.objects.select_related('current_stage').get(pk=selected_member_id)
                except (Member.DoesNotExist, ValueError, TypeError):
                    member = None

            if member and member.current_stage:
                stage_books = Book.objects.filter(stage=member.current_stage).select_related('stage').order_by('title')
                stage_book_ids = list(stage_books.values_list('id', flat=True))

                if self.instance.pk and self.instance.book_id and self.instance.book_id not in stage_book_ids:
                    stage_book_ids.append(self.instance.book_id)

                if stage_book_ids:
                    book_field.queryset = Book.objects.filter(pk__in=stage_book_ids).order_by('title')
            elif self.instance.pk and self.instance.book_id:
                book_field.queryset = Book.objects.filter(pk=self.instance.book_id)

            book_field.widget.attrs['data-dynamic-books'] = 'true'

        now_local = timezone.localtime()
        if not self.instance.pk:
            self.fields['assigned_date'].initial = now_local.strftime('%Y-%m-%dT%H:%M')
        else:
            if self.instance.assigned_date:
                self.fields['assigned_date'].initial = timezone.localtime(self.instance.assigned_date).strftime('%Y-%m-%dT%H:%M')
            if self.instance.due_date:
                self.fields['due_date'].initial = timezone.localtime(self.instance.due_date).strftime('%Y-%m-%dT%H:%M')
            if self.instance.returned_date:
                self.fields['returned_date'].initial = timezone.localtime(self.instance.returned_date).strftime('%Y-%m-%dT%H:%M')
            else:
                self.fields['returned_date'].initial = now_local.strftime('%Y-%m-%dT%H:%M')
            if self.instance.book and (not self.instance.quiz_score_earned):
                self.fields['quiz_score_earned'].initial = self.instance.book.quiz_score

        if not self.instance.pk:
            self.fields['returned_date'].initial = ''

        self.fields['assigned_date'].widget.attrs.setdefault('data-default-now', now_local.strftime('%Y-%m-%dT%H:%M'))
        self.fields['due_date'].widget.attrs['data-auto-due'] = 'true'
        self.fields['quiz_score_earned'].help_text = 'امتیاز پایه آزمون پس از انتخاب کتاب نمایش داده می‌شود'
        self.fields['quiz_score_earned'].widget.attrs['data-show-base'] = 'true'
        self.fields['quiz_score_earned'].widget.attrs.setdefault('min', 0)

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        book = cleaned_data.get('book')
        assigned_date = cleaned_data.get('assigned_date')
        due_date = cleaned_data.get('due_date')
        returned_date = cleaned_data.get('returned_date')

        if assigned_date is None:
            assigned_date = timezone.now()
            cleaned_data['assigned_date'] = assigned_date

        if timezone.is_naive(assigned_date):
            assigned_date = timezone.make_aware(assigned_date, timezone.get_current_timezone())
            cleaned_data['assigned_date'] = assigned_date

        if book:
            if due_date is None:
                due_date = assigned_date + timedelta(days=book.reading_days)
            if timezone.is_naive(due_date):
                due_date = timezone.make_aware(due_date, timezone.get_current_timezone())
            cleaned_data['due_date'] = due_date

            if member and getattr(member, 'current_stage', None) and book.stage_id != member.current_stage_id:
                self.add_error('book', 'کتاب انتخاب شده باید مربوط به مرحله فعلی عضو باشد.')

        if returned_date is not None:
            if timezone.is_naive(returned_date):
                returned_date = timezone.make_aware(returned_date, timezone.get_current_timezone())
            cleaned_data['returned_date'] = returned_date

        return cleaned_data

@admin.register(BookAssignment)
class BookAssignmentAdmin(admin.ModelAdmin):
    form = BookAssignmentAdminForm
    list_display = ['member', 'book', 'assigned_date_jalali', 'due_date_jalali', 'status', 'late_days', 'pages_read', 'penalty_display', 'scores']
    list_filter = ['is_completed', 'assigned_date', 'due_date', 'book__stage', 'late_days']
    search_fields = ['member__first_name', 'member__last_name', 'book__title']
    ordering = ['is_completed', '-assigned_date']
    readonly_fields = ['pages_read', 'penalty_preview']
    change_list_template = 'admin/books/bookassignment/change_list.html'
    change_form_template = 'admin/books/bookassignment/change_form.html'
    
    fieldsets = (
        ('اطلاعات امانت گرفتن', {
            'fields': ('member', 'book', 'assigned_date', 'due_date')
        }),
        ('اطلاعات بازگشت و امتیازات', {
            'fields': (
                'returned_date',
                'is_completed',
                'late_days',
                'reading_score_earned',
                'pages_read',
                'quiz_score_earned',
                'penalty_preview',
                'notes',
            )
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
        due_date = obj.due_date
        if due_date and timezone.now() > due_date:
            return format_html('<span style="color: red;">⚠ دیر شده</span>')
        return format_html('<span style="color: orange;">📖 در حال مطالعه</span>')
    status.short_description = "وضعیت"
    
    def penalty_display(self, obj):
        penalty = obj.penalty_amount if obj.is_completed else 0
        if penalty:
            return format_html('<span style="color:#d32f2f;">-{} امتیاز</span>', penalty)
        if obj.is_completed:
            return format_html('<span style="color:#388e3c;">بدون کسر</span>')
        return '-'
    penalty_display.short_description = "کسر امتیاز"

    def scores(self, obj):
        if obj.is_completed:
            return f"مطالعه: {obj.reading_score_earned} | آزمون: {obj.quiz_score_earned}"
        return "-"
    scores.short_description = "امتیازات"
    
    def save_model(self, request, obj, form, change):
        previous_instance = BookAssignment.objects.get(pk=obj.pk) if change else None

        if obj.returned_date and 'is_completed' not in form.changed_data:
            obj.is_completed = True
        elif not obj.returned_date and 'is_completed' not in form.changed_data:
            obj.is_completed = False

        if obj.book and 'quiz_score_earned' not in form.changed_data and obj.quiz_score_earned in (None, 0):
            obj.quiz_score_earned = obj.book.quiz_score

        computed_late_days = self._compute_late_days(obj)
        if 'late_days' not in form.changed_data:
            obj.late_days = computed_late_days

        if obj.book and 'reading_score_earned' not in form.changed_data:
            penalty_score = max(obj.book.reading_score - (obj.late_days or 0) * 2, 0)
            obj.reading_score_earned = penalty_score

        if obj.book:
            if obj.is_completed:
                obj.reading_score_base = obj.book.reading_score
                obj.quiz_score_base = obj.book.quiz_score
                obj.pages_read = obj.book.page_count or 0
            elif 'pages_read' not in form.changed_data:
                obj.pages_read = 0

        super().save_model(request, obj, form, change)

    class Media:
        js = ('js/admin-bookassignment.js',)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        current_assignment = self.get_object(request, object_id) if object_id else None

        BookAssignment.normalize_all_returned()

        active_books_qs = BookAssignment.objects.filter(is_completed=False)
        if current_assignment:
            active_books_qs = active_books_qs.exclude(pk=current_assignment.pk)
        active_counts = {
            row['book_id']: row['cnt']
            for row in active_books_qs.values('book_id').annotate(cnt=Count('id'))
        }

        books_queryset = Book.objects.select_related('stage').all()
        book_availability = {}
        books_payload = []
        for book in books_queryset:
            stock = book.stock_count or 0
            active_count = active_counts.get(book.id, 0)
            available = max(stock - active_count, 0)
            book_availability[book.id] = available
            books_payload.append({
                'id': book.id,
                'title': book.title,
                'reading_days': book.reading_days,
                'quiz_score': book.quiz_score,
                'stage_id': book.stage_id,
                'stock_count': stock,
                'available_copies': available,
            })

        members_payload = []
        members_queryset = Member.objects.filter(is_active=True).select_related('current_stage')
        for member in members_queryset:
            if member.current_stage:
                stage_books = Book.objects.filter(stage=member.current_stage).select_related('stage').order_by('title')
                stage_book_ids = [book.id for book in stage_books]
            else:
                stage_books = Book.objects.none()
                stage_book_ids = []

            completed_book_ids = list(BookAssignment.objects.filter(
                member=member,
                is_completed=True
            ).values_list('book_id', flat=True))

            filtered_book_ids = []
            for book in stage_books:
                if book.id in completed_book_ids:
                    continue
                if book_availability.get(book.id, 0) <= 0:
                    continue
                filtered_book_ids.append(book.id)

            available_book_ids = filtered_book_ids or []

            if current_assignment and current_assignment.member_id == member.id and current_assignment.book_id:
                if current_assignment.book_id not in available_book_ids:
                    available_book_ids.append(current_assignment.book_id)
                if current_assignment.book_id not in stage_book_ids:
                    stage_book_ids.append(current_assignment.book_id)

            members_payload.append({
                'id': member.id,
                'stage_id': member.current_stage_id,
                'stage_name': member.current_stage.name if member.current_stage else '',
                'stage_book_ids': stage_book_ids,
                'available_book_ids': available_book_ids,
                'completed_book_ids': completed_book_ids,
            })

        extra_context['book_assignment_meta'] = {
            'now': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'current_member_id': current_assignment.member_id if current_assignment else None,
            'current_book_id': current_assignment.book_id if current_assignment else None,
            'books': books_payload,
            'members': members_payload,
            'max_initial_options': 3,
        }
        return super().changeform_view(request, object_id, form_url, extra_context)

    def penalty_preview(self, obj):
        if not obj or not obj.book:
            return 'بدون اطلاعات'
        penalty = obj.penalty_amount if obj.is_completed else 0
        total = obj.book.reading_score
        if penalty:
            return format_html('کسر شده: <strong style="color:#d32f2f;">{} امتیاز</strong> از {} امتیاز مطالعه', penalty, total)
        if obj.is_completed:
            return format_html('<strong style="color:#388e3c;">امتیاز کامل ({})</strong>', total)
        return format_html('پس از تکمیل، کسر امتیاز اینجا نمایش داده می‌شود')
    penalty_preview.short_description = "وضعیت امتیاز مطالعه"

    def _compute_late_days(self, assignment):
        if assignment.returned_date and assignment.due_date:
            returned_dt = timezone.localtime(assignment.returned_date) if timezone.is_aware(assignment.returned_date) else assignment.returned_date
            due_dt = timezone.localtime(assignment.due_date) if timezone.is_aware(assignment.due_date) else assignment.due_date
            if returned_dt > due_dt:
                return max((returned_dt - due_dt).days, 0)
        return 0

    def _apply_score_delta(self, member, delta, reference_datetime):
        if not member or delta == 0:
            return

        member.total_score = max(member.total_score + delta, 0)
        member.save(update_fields=['total_score'])

        if not reference_datetime:
            return

        week_start, week_end = self._week_bounds(reference_datetime)
        if week_start is None:
            return

        try:
            weekly = WeeklyScore.objects.get(member=member, week_start_date=week_start)
        except WeeklyScore.DoesNotExist:
            if delta > 0:
                WeeklyScore.objects.create(
                    member=member,
                    week_start_date=week_start,
                    week_end_date=week_end,
                    weekly_score=max(delta, 0)
                )
            return

        weekly.weekly_score = max(weekly.weekly_score + delta, 0)
        weekly.week_end_date = week_end
        weekly.save(update_fields=['weekly_score', 'week_end_date'])

    @staticmethod
    def _week_bounds(reference_datetime):
        if not reference_datetime:
            return None, None

        if timezone.is_aware(reference_datetime):
            local_dt = timezone.localtime(reference_datetime)
        else:
            local_dt = reference_datetime

        base_date = local_dt.date()
        days_since_saturday = (base_date.weekday() + 2) % 7
        week_start = base_date - timedelta(days=days_since_saturday)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

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


class NotificationAdminForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['notification_type', 'recipient', 'title', 'message', 'is_read']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        notif_type = cleaned_data.get('notification_type')
        recipient = cleaned_data.get('recipient')

        if notif_type == Notification.TYPE_PRIVATE and not recipient:
            self.add_error('recipient', 'برای اعلان خصوصی باید گیرنده را انتخاب کنید.')

        if notif_type == Notification.TYPE_GENERAL:
            cleaned_data['recipient'] = None
            cleaned_data['is_read'] = False

        return cleaned_data


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    form = NotificationAdminForm
    list_display = ['title', 'notification_type', 'recipient', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__username', 'recipient__first_name', 'recipient__last_name']
    autocomplete_fields = ['recipient']
    readonly_fields = ['created_at', 'is_read']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('notification_type', 'recipient', 'title', 'message')
        }),
        ('وضعیت', {
            'fields': ('is_read',),
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.is_staff:
            readonly.append('notification_type')
        return readonly

    def save_model(self, request, obj, form, change):
        if obj.notification_type == Notification.TYPE_GENERAL:
            obj.recipient = None
            obj.is_read = False
        elif obj.notification_type == Notification.TYPE_PRIVATE:
            obj.is_read = False
        super().save_model(request, obj, form, change)
