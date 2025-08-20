from django.urls import path
from . import views

app_name = 'reading_sessions'

urlpatterns = [
    path('handout/<int:book_id>/', views.handout_book, name='handout_book'),
    path('return/<int:handout_id>/', views.return_book, name='return_book'),
    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
]
