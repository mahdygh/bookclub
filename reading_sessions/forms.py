from django import forms
from .models import BookHandout, BookReturn, Quiz, QuizQuestion, QuizChoice


class BookHandoutForm(forms.ModelForm):
    """فرم تحویل کتاب"""
    class Meta:
        model = BookHandout
        fields = ['member', 'notes']
        widgets = {
            'member': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'انتخاب عضو'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'یادداشت‌ها (اختیاری)'
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


class QuizForm(forms.Form):
    """فرم آزمون"""
    
    def __init__(self, *args, **kwargs):
        quiz = kwargs.pop('quiz', None)
        super().__init__(*args, **kwargs)
        
        if quiz:
            for question in quiz.questions.all():
                if question.question_type == 'multiple_choice':
                    choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        choices=choices,
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                        label=question.question_text,
                        required=True
                    )
                elif question.question_type == 'true_false':
                    choices = [('True', 'درست'), ('False', 'غلط')]
                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        choices=choices,
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                        label=question.question_text,
                        required=True
                    )
                elif question.question_type == 'short_answer':
                    self.fields[f'question_{question.id}'] = forms.CharField(
                        widget=forms.TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'پاسخ خود را بنویسید...'
                        }),
                        label=question.question_text,
                        required=True
                    )
    
    def calculate_score(self):
        """محاسبه امتیاز آزمون"""
        total_score = 0
        total_possible = 0
        
        for field_name, field_value in self.cleaned_data.items():
            if field_name.startswith('question_'):
                question_id = int(field_name.split('_')[1])
                try:
                    question = QuizQuestion.objects.get(id=question_id)
                    total_possible += question.points
                    
                    if question.question_type == 'multiple_choice':
                        try:
                            selected_choice = QuizChoice.objects.get(id=field_value)
                            if selected_choice.is_correct:
                                total_score += question.points
                        except QuizChoice.DoesNotExist:
                            pass
                    elif question.question_type == 'true_false':
                        # برای سوالات درست/غلط، امتیاز کامل می‌دهیم
                        # در حالت واقعی باید پاسخ صحیح تعریف شود
                        total_score += question.points
                    elif question.question_type == 'short_answer':
                        # برای سوالات تشریحی، امتیاز کامل می‌دهیم
                        # در حالت واقعی باید پاسخ صحیح تعریف شود
                        total_score += question.points
                        
                except QuizQuestion.DoesNotExist:
                    pass
        
        if total_possible > 0:
            return int((total_score / total_possible) * 100)
        return 0
