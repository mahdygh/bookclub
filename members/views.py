from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import MemberProfileForm


@login_required
def profile(request):
    """نمایش پروفایل کاربر"""
    return render(request, 'members/profile.html')


@login_required
def edit_profile(request):
    """ویرایش پروفایل کاربر"""
    if request.method == 'POST':
        form = MemberProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
            return redirect('members:profile')
    else:
        form = MemberProfileForm(instance=request.user.profile)
    
    context = {
        'form': form,
    }
    return render(request, 'members/edit_profile.html', context)
