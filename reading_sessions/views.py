from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BookHandout, BookReturn, Quiz, QuizAttempt
from .forms import BookHandoutForm, BookReturnForm, QuizForm


@login_required
def handout_book(request, book_id):
    """تحویل کتاب به عضو"""
    if not request.user.is_staff:
        messages.error(request, 'شما مجوز انجام این کار را ندارید.')
        return redirect('books:home')
    
    from books.models import Book
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        form = BookHandoutForm(request.POST)
        if form.is_valid():
            handout = form.save(commit=False)
            handout.book = book
            handout.save()
            
            messages.success(request, f'کتاب {book.title} با موفقیت تحویل داده شد.')
            return redirect('books:book_detail', book_id=book_id)
    else:
        form = BookHandoutForm()
    
    context = {
        'form': form,
        'book': book,
    }
    return render(request, 'reading_sessions/handout_book.html', context)


@login_required
def return_book(request, handout_id):
    """تحویل گرفتن کتاب از عضو"""
    if not request.user.is_staff:
        messages.error(request, 'شما مجوز انجام این کار را ندارید.')
        return redirect('books:home')
    
    handout = get_object_or_404(BookHandout, id=handout_id)
    
    if request.method == 'POST':
        form = BookReturnForm(request.POST)
        if form.is_valid():
            book_return = form.save(commit=False)
            book_return.handout = handout
            book_return.save()
            
            messages.success(request, f'کتاب {handout.book.title} با موفقیت تحویل گرفته شد.')
            return redirect('books:home')
    else:
        form = BookReturnForm()
    
    context = {
        'form': form,
        'handout': handout,
    }
    return render(request, 'reading_sessions/return_book.html', context)


@login_required
def take_quiz(request, quiz_id):
    """شرکت در آزمون"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # بررسی اینکه آیا کاربر قبلاً در این آزمون شرکت کرده یا نه
    try:
        attempt = QuizAttempt.objects.get(quiz=quiz, member=request.user.member)
        if attempt.is_completed:
            messages.info(request, 'شما قبلاً در این آزمون شرکت کرده‌اید.')
            return redirect('books:home')
    except QuizAttempt.DoesNotExist:
        attempt = QuizAttempt.objects.create(quiz=quiz, member=request.user.member)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, quiz=quiz)
        if form.is_valid():
            # محاسبه امتیاز
            score = form.calculate_score()
            attempt.score = score
            attempt.is_completed = True
            attempt.save()
            
            messages.success(request, f'آزمون شما با امتیاز {score} تکمیل شد.')
            return redirect('books:home')
    else:
        form = QuizForm(quiz=quiz)
    
    context = {
        'form': form,
        'quiz': quiz,
        'attempt': attempt,
    }
    return render(request, 'reading_sessions/take_quiz.html', context)
