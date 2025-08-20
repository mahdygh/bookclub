from django import forms
from .models import MemberProfile


class MemberProfileForm(forms.ModelForm):
    """فرم ویرایش پروفایل عضو"""
    class Meta:
        model = MemberProfile
        fields = ['phone', 'bio', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تلفن'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'بیوگرافی خود را بنویسید...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
