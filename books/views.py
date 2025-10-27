from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.http import JsonResponse
from .models import ReadingPeriod, Stage, Book, Member, BookAssignment
import re

def generate_username(member):
    """تولید نام کاربری بر اساس فرمت: حرف اول اسم + . + فامیلی + 313"""
    # تبدیل نام و نام خانوادگی به لاتین
    first_name_latin = convert_to_latin(member.first_name or '')
    last_name_latin = convert_to_latin(member.last_name or '')
    
    if not first_name_latin or not last_name_latin:
        # اگر نام یا نام خانوادگی خالی باشد، از نام کامل استفاده کن
        full_name = convert_to_latin(member.full_name or '')
        if full_name:
            # اگر فقط یک کلمه باشد، آن را به عنوان نام خانوادگی در نظر بگیر
            if ' ' not in full_name:
                last_name_latin = full_name
                first_name_latin = full_name[0] if full_name else 'u'
            else:
                parts = full_name.split()
                first_name_latin = parts[0] if parts else 'u'
                last_name_latin = parts[-1] if len(parts) > 1 else parts[0]
        else:
            first_name_latin = 'user'
            last_name_latin = 'member'
    
    # حرف اول نام
    first_letter = first_name_latin[0].lower() if first_name_latin else 'u'
    
    # نام خانوادگی کامل
    last_name_clean = last_name_latin.lower().replace(' ', '')
    
    # تولید نام کاربری
    username = f"{first_letter}.{last_name_clean}313"
    
    # بررسی تکراری بودن
    counter = 1
    original_username = username
    while User.objects.filter(username=username).exists():
        username = f"{original_username}{counter}"
        counter += 1
    
    return username

def convert_to_latin(persian_text):
    """تبدیل متن فارسی به لاتین"""
    if not persian_text:
        return ''
    
    # جدول تبدیل حروف فارسی به لاتین
    persian_to_latin = {
        'ا': 'a', 'آ': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's', 'ج': 'j', 'چ': 'ch',
        'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z', 'ژ': 'zh', 'س': 's',
        'ش': 'sh', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh', 'ف': 'f',
        'ق': 'gh', 'ک': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n', 'و': 'v', 'ه': 'h',
        'ی': 'i', 'ئ': 'e', 'ء': 'e', 'ؤ': 'o', 'أ': 'a', 'إ': 'e', 'ة': 'h',
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    
    # تبدیل حروف
    latin_text = ''
    for char in persian_text:
        if char in persian_to_latin:
            latin_text += persian_to_latin[char]
        elif char.isalpha():
            latin_text += char.lower()
        elif char == ' ':
            latin_text += ' '
    
    # پاک کردن فضاهای اضافی
    latin_text = re.sub(r'\s+', ' ', latin_text).strip()
    
    return latin_text

def home(request):
    """صفحه اصلی"""
    try:
        active_period = ReadingPeriod.objects.get(is_active=True)
        stages = Stage.objects.filter(period=active_period).order_by('order')
        
        # آمار کلی
        total_members = Member.objects.filter(is_active=True).count()
        total_books = Book.objects.filter(stage__period=active_period).count()
        completed_books = BookAssignment.objects.filter(
            book__stage__period=active_period,
            is_completed=True
        ).count()
        
        # چک کردن پیام خوش‌آمدگویی
        show_welcome = request.session.pop('just_logged_in', False)
        
        context = {
            'active_period': active_period,
            'stages': stages,
            'total_members': total_members,
            'total_books': total_books,
            'completed_books': completed_books,
            'show_welcome': show_welcome,
        }
    except ReadingPeriod.DoesNotExist:
        context = {
            'active_period': None,
            'stages': [],
            'total_members': 0,
            'total_books': 0,
            'completed_books': 0,
            'show_welcome': False,
        }
    
    return render(request, 'books/home_modern.html', context)

def stage_books(request, stage_id):
    """نمایش کتاب‌های یک مرحله"""
    stage = get_object_or_404(Stage, id=stage_id)
    books = Book.objects.filter(stage=stage).order_by('title')
    
    # آمار مرحله
    stage_members = Member.objects.filter(current_stage=stage, is_active=True)
    stage_stats = {
        'total_members': stage_members.count(),
        'completed_members': sum(1 for m in stage_members if m.can_advance_to_next_stage()),
        'total_books': books.count(),
    }
    
    context = {
        'stage': stage,
        'books': books,
        'stats': stage_stats,
    }
    return render(request, 'books/stage_books_modern.html', context)

def book_detail(request, book_id):
    """جزئیات کتاب"""
    book = get_object_or_404(Book, id=book_id)
    
    # تخصیص‌های این کتاب
    assignments = BookAssignment.objects.filter(book=book).select_related('member').order_by('-assigned_date')
    
    context = {
        'book': book,
        'assignments': assignments,
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def rankings(request):
    """رتبه‌بندی کلی"""
    from datetime import date, timedelta
    from .models import WeeklyScore
    
    # دریافت عضو مرتبط با کاربر
    try:
        current_member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        current_member = None
    
    try:
        active_period = ReadingPeriod.objects.get(is_active=True)
        
        # رتبه‌بندی کلی
        from django.db.models import Q
        overall_rankings = Member.objects.filter(
            is_active=True
        ).annotate(
            total_books_completed=Count('bookassignment', filter=Q(bookassignment__is_completed=True))
        ).order_by('-total_score')
        
        # رتبه‌بندی هفتگی
        today = date.today()
        days_since_saturday = (today.weekday() + 2) % 7
        week_start = today - timedelta(days=days_since_saturday)
        
        weekly_rankings = WeeklyScore.objects.filter(
            week_start_date=week_start,
            member__is_active=True
        ).select_related('member').order_by('-weekly_score')
        
        # اضافه کردن اطلاعات کتاب‌های تکمیل شده به هر عضو
        for weekly in weekly_rankings:
            weekly.member.total_books_completed = BookAssignment.objects.filter(
                member=weekly.member,
                is_completed=True
            ).count()
        
        # رتبه‌بندی گروه (فقط گروه خود کاربر)
        user_group_rankings = []
        if current_member:
            user_group_rankings = Member.objects.filter(
                is_active=True,
                group=current_member.group
            ).annotate(
                total_books_completed=Count('bookassignment', filter=Q(bookassignment__is_completed=True))
            ).order_by('-total_score')
        
        # رتبه‌بندی مراحل
        stages = Stage.objects.filter(period=active_period).order_by('order')
        stage_rankings = {}
        
        for stage in stages:
            stage_members = Member.objects.filter(
                current_stage=stage,
                is_active=True
            ).annotate(
                reading_score_sum=Sum('bookassignment__reading_score_earned'),
                quiz_score_sum=Sum('bookassignment__quiz_score_earned')
            ).order_by('-total_score')
            
            # محاسبه امتیاز مرحله برای هر عضو
            for member in stage_members:
                reading = member.reading_score_sum or 0
                quiz = member.quiz_score_sum or 0
                member.stage_score = reading + quiz
            
            stage_rankings[stage] = stage_members
        
        context = {
            'active_period': active_period,
            'overall_rankings': overall_rankings,
            'weekly_rankings': weekly_rankings,
            'user_group_rankings': user_group_rankings,
            'current_member': current_member,
            'stage_rankings': stage_rankings,
            'week_start': week_start,
        }
    except ReadingPeriod.DoesNotExist:
        context = {
            'active_period': None,
            'overall_rankings': [],
            'weekly_rankings': [],
            'user_group_rankings': [],
            'current_member': current_member,
            'stage_rankings': {},
        }
    
    return render(request, 'books/rankings_modern.html', context)

def stage_rankings(request, stage_id):
    """رتبه‌بندی یک مرحله خاص"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    rankings = Member.objects.filter(
        current_stage=stage,
        is_active=True
    ).annotate(
        reading_score_sum=Sum('bookassignment__reading_score_earned'),
        quiz_score_sum=Sum('bookassignment__quiz_score_earned')
    ).order_by('-total_score')
    
    # محاسبه امتیاز مرحله برای هر عضو
    for member in rankings:
        reading = member.reading_score_sum or 0
        quiz = member.quiz_score_sum or 0
        member.stage_score = reading + quiz
    
    context = {
        'stage': stage,
        'rankings': rankings,
    }
    return render(request, 'books/stage_rankings_modern.html', context)

def member_progress(request, member_id):
    """پیشرفت یک عضو خاص"""
    member = get_object_or_404(Member, id=member_id)
    
    if not member.current_stage:
        messages.warning(request, 'این عضو هنوز مرحله‌ای تعیین نشده است.')
        return redirect('books:rankings')
    
    # کتاب‌های مرحله فعلی
    stage_books = Book.objects.filter(stage=member.current_stage).order_by('title')
    
    # امانت‌های این عضو در مرحله فعلی
    assignments = BookAssignment.objects.filter(
        member=member,
        book__stage=member.current_stage
    ).select_related('book').order_by('book__title')
    
    # آمار پیشرفت
    progress_stats = {
        'total_books': member.get_total_books_in_stage(),
        'completed_books': member.get_completed_books_count(),
        'progress_percentage': member.get_stage_progress_percentage(),
        'can_advance': member.can_advance_to_next_stage(),
    }
    
    # کتاب‌های خوانده شده و نخوانده
    completed_books = []
    uncompleted_books = []
    
    for book in stage_books:
        assignment = assignments.filter(book=book).first()
        if assignment and assignment.is_completed:
            completed_books.append({
                'book': book,
                'assignment': assignment,
                'score': assignment.reading_score_earned + assignment.quiz_score_earned
            })
        else:
            uncompleted_books.append({
                'book': book,
                'assignment': assignment
            })
    
    context = {
        'member': member,
        'stage': member.current_stage,
        'progress_stats': progress_stats,
        'completed_books': completed_books,
        'uncompleted_books': uncompleted_books,
        'assignments': assignments,
    }
    
    return render(request, 'books/member_progress.html', context)

def assign_book(request):
    """امانت گرفتن کتاب توسط عضو (فقط برای نمایش)"""
    if request.method == 'POST':
        # این بخش فقط برای نمایش است - عملیات در admin انجام می‌شود
        messages.info(request, 'امانت گرفتن کتاب از طریق پنل ادمین انجام می‌شود.')
        return redirect('books:home')
    
    # نمایش فرم امانت گرفتن
    members = Member.objects.filter(is_active=True).order_by('first_name')
    books = Book.objects.all().order_by('stage__order', 'title')
    active_assignments = BookAssignment.objects.filter(is_completed=False).count()
    completed_assignments = BookAssignment.objects.filter(is_completed=True).count()
    
    context = {
        'members': members,
        'books': books,
        'active_assignments': active_assignments,
        'completed_assignments': completed_assignments,
    }
    return render(request, 'books/assign_book.html', context)

def return_book(request):
    """بازگشت کتاب (فقط برای نمایش)"""
    if request.method == 'POST':
        # این بخش فقط برای نمایش است - عملیات در admin انجام می‌شود
        messages.info(request, 'بازگشت کتاب از طریق پنل ادمین انجام می‌شود.')
        return redirect('books:home')
    
    # نمایش فرم بازگشت
    from datetime import date
    today = date.today()
    
    active_assignments = BookAssignment.objects.filter(
        is_completed=False
    ).select_related('member', 'book').order_by('-assigned_date')
    
    completed_assignments = BookAssignment.objects.filter(
        is_completed=True
    ).select_related('member', 'book').order_by('-returned_date')
    
    overdue_assignments = BookAssignment.objects.filter(
        is_completed=False,
        due_date__lt=today
    ).select_related('member', 'book').order_by('-assigned_date')
    
    context = {
        'active_assignments': active_assignments,
        'completed_assignments': completed_assignments,
        'overdue_assignments': overdue_assignments,
        'today': today,
    }
    return render(request, 'books/return_book.html', context)

def admin_member_progress(request):
    """صفحه ادمین برای نمایش وضعیت مطالعه اعضا"""
    # بررسی دسترسی ادمین
    if not request.user.is_staff:
        messages.error(request, 'شما دسترسی به این صفحه ندارید.')
        return redirect('books:home')
    try:
        active_period = ReadingPeriod.objects.get(is_active=True)
        stages = Stage.objects.filter(period=active_period).order_by('order')
        
        # دریافت تمام اعضای فعال
        members = Member.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # آمار کلی
        total_members = members.count()
        total_books = Book.objects.filter(stage__period=active_period).count()
        
        # اطلاعات تفصیلی هر عضو
        member_details = []
        for member in members:
            # کتاب‌های مرحله فعلی
            stage_books = Book.objects.filter(stage=member.current_stage) if member.current_stage else Book.objects.none()
            
            # امانت‌های این عضو
            assignments = BookAssignment.objects.filter(
                member=member,
                book__stage__period=active_period
            ).select_related('book', 'book__stage').order_by('book__stage__order', 'book__title')
            
            # کتاب‌های خوانده شده و نخوانده
            completed_books = []
            uncompleted_books = []
            
            for book in stage_books:
                assignment = assignments.filter(book=book).first()
                if assignment and assignment.is_completed:
                    completed_books.append({
                        'book': book,
                        'assignment': assignment,
                        'score': assignment.reading_score_earned + assignment.quiz_score_earned,
                        'returned_date': assignment.returned_date
                    })
                else:
                    uncompleted_books.append({
                        'book': book,
                        'assignment': assignment
                    })
            
            # آمار پیشرفت
            progress_stats = {
                'total_books_in_stage': member.get_total_books_in_stage(),
                'completed_books': member.get_completed_books_count(),
                'progress_percentage': member.get_stage_progress_percentage(),
                'can_advance': member.can_advance_to_next_stage(),
            }
            
            member_details.append({
                'member': member,
                'stage': member.current_stage,
                'completed_books': completed_books,
                'uncompleted_books': uncompleted_books,
                'progress_stats': progress_stats,
                'total_assignments': assignments.count(),
                'completed_assignments': assignments.filter(is_completed=True).count(),
            })
        
        context = {
            'active_period': active_period,
            'stages': stages,
            'members': members,
            'member_details': member_details,
            'total_members': total_members,
            'total_books': total_books,
        }
        
    except ReadingPeriod.DoesNotExist:
        context = {
            'active_period': None,
            'stages': [],
            'members': [],
            'member_details': [],
            'total_members': 0,
            'total_books': 0,
        }
    
    return render(request, 'books/admin_member_progress.html', context)

@login_required
def user_progress(request):
    """صفحه کاربر عادی برای نمایش وضعیت مطالعه خودش"""
    
    try:
        # پیدا کردن عضو مربوط به کاربر
        try:
            member = Member.objects.get(user=request.user)
        except Member.DoesNotExist:
            messages.error(request, 'عضو مربوط به شما یافت نشد.')
            return redirect('books:home')
        
        active_period = ReadingPeriod.objects.get(is_active=True)
        
        # کتاب‌های مرحله فعلی
        stage_books = Book.objects.filter(stage=member.current_stage) if member.current_stage else Book.objects.none()
        
        # امانت‌های این عضو
        assignments = BookAssignment.objects.filter(
            member=member,
            book__stage__period=active_period
        ).select_related('book', 'book__stage').order_by('book__stage__order', 'book__title')
        
        # کتاب‌های خوانده شده و نخوانده
        completed_books = []
        uncompleted_books = []
        
        for book in stage_books:
            assignment = assignments.filter(book=book).first()
            if assignment and assignment.is_completed:
                completed_books.append({
                    'book': book,
                    'assignment': assignment,
                    'score': assignment.reading_score_earned + assignment.quiz_score_earned,
                    'returned_date': assignment.returned_date
                })
            else:
                uncompleted_books.append({
                    'book': book,
                    'assignment': assignment
                })
        
        # آمار پیشرفت
        progress_stats = {
            'total_books_in_stage': member.get_total_books_in_stage(),
            'completed_books': member.get_completed_books_count(),
            'progress_percentage': member.get_stage_progress_percentage(),
            'can_advance': member.can_advance_to_next_stage(),
        }
        
        # محاسبه رتبه‌ها
        from datetime import date, timedelta
        from .models import WeeklyScore
        
        # رتبه کلی
        overall_rank = Member.objects.filter(
            is_active=True,
            total_score__gt=member.total_score
        ).count() + 1
        
        # رتبه در گروه
        group_rank = Member.objects.filter(
            is_active=True,
            group=member.group,
            total_score__gt=member.total_score
        ).count() + 1
        
        # رتبه هفتگی
        today = date.today()
        days_since_saturday = (today.weekday() + 2) % 7
        week_start = today - timedelta(days=days_since_saturday)
        
        # دریافت امتیاز هفتگی عضو
        try:
            member_weekly = WeeklyScore.objects.get(member=member, week_start_date=week_start)
            member_weekly_score = member_weekly.weekly_score
        except WeeklyScore.DoesNotExist:
            member_weekly_score = 0
        
        # محاسبه رتبه هفتگی
        weekly_rank = WeeklyScore.objects.filter(
            week_start_date=week_start,
            member__is_active=True,
            weekly_score__gt=member_weekly_score
        ).count() + 1
        
        # تعداد کل اعضای فعال
        total_members = Member.objects.filter(is_active=True).count()
        total_group_members = Member.objects.filter(is_active=True, group=member.group).count()
        total_weekly_members = WeeklyScore.objects.filter(week_start_date=week_start, member__is_active=True).count()
        
        rankings = {
            'overall_rank': overall_rank,
            'group_rank': group_rank,
            'weekly_rank': weekly_rank,
            'weekly_score': member_weekly_score,
            'total_members': total_members,
            'total_group_members': total_group_members,
            'total_weekly_members': total_weekly_members,
        }
        
        # چک کردن اینکه آیا از صفحه لاگین آمده یا نه
        show_welcome = request.session.pop('just_logged_in', False)
        
        context = {
            'active_period': active_period,
            'member': member,
            'stage': member.current_stage,
            'completed_books': completed_books,
            'uncompleted_books': uncompleted_books,
            'progress_stats': progress_stats,
            'rankings': rankings,
            'total_assignments': assignments.count(),
            'completed_assignments': assignments.filter(is_completed=True).count(),
            'show_welcome': show_welcome,
        }
        
    except ReadingPeriod.DoesNotExist:
        context = {
            'active_period': None,
            'member': None,
            'stage': None,
            'completed_books': [],
            'uncompleted_books': [],
            'progress_stats': {},
            'total_assignments': 0,
            'completed_assignments': 0,
        }
    
    return render(request, 'books/user_progress_modern.html', context)

def api_member_details(request, member_id):
    """API برای دریافت جزئیات یک عضو"""
    try:
        member = Member.objects.get(id=member_id, is_active=True)
        
        # کتاب‌های مرحله فعلی
        stage_books = Book.objects.filter(stage=member.current_stage) if member.current_stage else Book.objects.none()
        
        # امانت‌های این عضو
        assignments = BookAssignment.objects.filter(
            member=member,
            book__stage__period__is_active=True
        ).select_related('book', 'book__stage').order_by('book__stage__order', 'book__title')
        
        # کتاب‌های خوانده شده و نخوانده
        completed_books = []
        uncompleted_books = []
        
        for book in stage_books:
            assignment = assignments.filter(book=book).first()
            if assignment and assignment.is_completed:
                completed_books.append({
                    'title': book.title,
                    'author': book.author,
                    'score': assignment.reading_score_earned + assignment.quiz_score_earned,
                    'returned_date': assignment.returned_date.strftime('%Y/%m/%d') if assignment.returned_date else ''
                })
            else:
                uncompleted_books.append({
                    'title': book.title,
                    'author': book.author,
                    'assignment': assignment is not None,
                    'due_date': assignment.due_date.strftime('%Y/%m/%d') if assignment and assignment.due_date else ''
                })
        
        data = {
            'name': member.full_name,
            'completed_books': completed_books,
            'uncompleted_books': uncompleted_books,
        }
        
        return JsonResponse(data)
        
    except Member.DoesNotExist:
        return JsonResponse({'error': 'عضو یافت نشد'}, status=404)

def api_rankings(request):
    """API برای رتبه‌بندی (برای نمودارها)"""
    try:
        active_period = ReadingPeriod.objects.get(is_active=True)
        
        # رتبه‌بندی کلی
        overall = Member.objects.filter(
            is_active=True
        ).values(
            'first_name', 'last_name', 'total_score'
        ).order_by('-total_score')[:10]
        
        # رتبه‌بندی مراحل
        stages = Stage.objects.filter(period=active_period).order_by('order')
        stage_data = {}
        
        for stage in stages:
            stage_members = Member.objects.filter(
                current_stage=stage,
                is_active=True
            ).annotate(
                stage_score=Sum('bookassignment__reading_score_earned') + Sum('bookassignment__quiz_score_earned')
            ).values('first_name', 'last_name', 'stage_score').order_by('-stage_score')[:5]
            
            stage_data[stage.name] = list(stage_members)
        
        data = {
            'overall': list(overall),
            'stages': stage_data,
        }
        
        return JsonResponse(data)
        
    except ReadingPeriod.DoesNotExist:
        return JsonResponse({'error': 'دوره فعالی یافت نشد'}, status=404)

def user_login(request):
    """صفحه ورود کاربران عادی"""
    if request.user.is_authenticated:
        return redirect('books:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # تنظیم flag برای نمایش پیام خوش‌آمدگویی
                request.session['just_logged_in'] = True
                next_url = request.GET.get('next', 'books:home')
                return redirect(next_url)
            else:
                messages.error(request, 'نام کاربری و رمز عبور اشتباه است. برای دریافت نام کاربری و رمز عبور به مربی مراجعه کنید.')
        else:
            messages.error(request, 'لطفاً تمام فیلدها را پر کنید.')
    
    return render(request, 'books/login.html')

def user_logout(request):
    """خروج کاربر"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('books:home')

@login_required
def manage_members(request):
    """مدیریت اعضا و اتصال به یوزرها"""
    if not request.user.is_staff:
        messages.error(request, 'شما دسترسی به این صفحه ندارید.')
        return redirect('books:home')
    
    members = Member.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        member_id = request.POST.get('member_id')
        
        if action == 'create_user' and member_id:
            member = get_object_or_404(Member, id=member_id)
            
            # تولید خودکار نام کاربری و رمز عبور
            username = generate_username(member)
            password = 'masjedhoori'
            email = request.POST.get('email', '')
            
            success, message = member.create_user_account(username, password, email)
            if success:
                messages.success(request, f'{message} - نام کاربری: {username} - رمز عبور: {password}')
            else:
                messages.error(request, message)
        
        elif action == 'update_user' and member_id:
            member = get_object_or_404(Member, id=member_id)
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            
            success, message = member.update_user_info(first_name, last_name, email)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
        
        elif action == 'delete_user' and member_id:
            member = get_object_or_404(Member, id=member_id)
            if member.user:
                member.user.delete()
                member.user = None
                member.save()
                messages.success(request, 'حساب کاربری حذف شد.')
            else:
                messages.error(request, 'این عضو حساب کاربری ندارد.')
        
        return redirect('books:manage_members')
    
    context = {
        'members': members,
    }
    return render(request, 'books/manage_members.html', context)

