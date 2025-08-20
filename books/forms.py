from django import forms
from .models import BookAssignment
from reading_sessions.models import BookReturn


class BookAssignmentForm(forms.ModelForm):
    """فرم تخصیص کتاب"""
    class Meta:
        model = BookAssignment
        fields = ['member']
        widgets = {
            'member': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'انتخاب عضو'
            })
        }


class BookReturnForm(forms.ModelForm):
    """فرم تحویل گرفتن کتاب"""
    quiz_score = forms.IntegerField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'امتیاز آزمون (0-100)'
        }),
        label='امتیاز آزمون'
    )
    
    class Meta:
        model = BookReturn
        fields = ['quiz_score', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'یادداشت‌ها (اختیاری)'
            })
        }
