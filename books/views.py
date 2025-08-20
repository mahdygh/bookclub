from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Sum
from django.http import JsonResponse
from .models import ReadingPeriod, Stage, Book, Member, BookAssignment

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
        
        context = {
            'active_period': active_period,
            'stages': stages,
            'total_members': total_members,
            'total_books': total_books,
            'completed_books': completed_books,
        }
    except ReadingPeriod.DoesNotExist:
        context = {
            'active_period': None,
            'stages': [],
            'total_members': 0,
            'total_books': 0,
            'completed_books': 0,
        }
    
    return render(request, 'books/home.html', context)

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
    return render(request, 'books/stage_books.html', context)

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

def rankings(request):
    """رتبه‌بندی کلی"""
    try:
        active_period = ReadingPeriod.objects.get(is_active=True)
        
        # رتبه‌بندی کلی
        overall_rankings = Member.objects.filter(
            is_active=True
        ).annotate(
            total_books_completed=Count('bookassignment', filter={'bookassignment__is_completed': True})
        ).order_by('-total_score')
        
        # رتبه‌بندی مراحل
        stages = Stage.objects.filter(period=active_period).order_by('order')
        stage_rankings = {}
        
        for stage in stages:
            stage_members = Member.objects.filter(
                current_stage=stage,
                is_active=True
            ).annotate(
                stage_score=Sum('bookassignment__reading_score_earned') + Sum('bookassignment__quiz_score_earned')
            ).order_by('-stage_score')
            stage_rankings[stage] = stage_members
        
        context = {
            'active_period': active_period,
            'overall_rankings': overall_rankings,
            'stage_rankings': stage_rankings,
        }
    except ReadingPeriod.DoesNotExist:
        context = {
            'active_period': None,
            'overall_rankings': [],
            'stage_rankings': {},
        }
    
    return render(request, 'books/rankings.html', context)

def stage_rankings(request, stage_id):
    """رتبه‌بندی یک مرحله خاص"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    rankings = Member.objects.filter(
        current_stage=stage,
        is_active=True
    ).annotate(
        stage_score=Sum('bookassignment__reading_score_earned') + Sum('bookassignment__quiz_score_earned')
    ).order_by('-stage_score')
    
    context = {
        'stage': stage,
        'rankings': rankings,
    }
    return render(request, 'books/stage_rankings.html', context)

def member_progress(request, member_id):
    """پیشرفت یک عضو خاص"""
    member = get_object_or_404(Member, id=member_id)
    
    if not member.current_stage:
        messages.warning(request, 'این عضو هنوز مرحله‌ای تعیین نشده است.')
        return redirect('books:rankings')
    
    # کتاب‌های مرحله فعلی
    stage_books = Book.objects.filter(stage=member.current_stage).order_by('title')
    
    # تخصیص‌های این عضو در مرحله فعلی
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
    """تخصیص کتاب به عضو (فقط برای نمایش)"""
    if request.method == 'POST':
        # این بخش فقط برای نمایش است - عملیات در admin انجام می‌شود
        messages.info(request, 'تخصیص کتاب از طریق پنل ادمین انجام می‌شود.')
        return redirect('books:home')
    
    # نمایش فرم تخصیص
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
