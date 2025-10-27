from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('manage-members/', views.manage_members, name='manage_members'),
    path('stage/<int:stage_id>/', views.stage_books, name='stage_books'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('rankings/', views.rankings, name='rankings'),
    path('stage/<int:stage_id>/rankings/', views.stage_rankings, name='stage_rankings'),
    path('member/<int:member_id>/progress/', views.member_progress, name='member_progress'),
    path('assign-book/', views.assign_book, name='assign_book'),
    path('return-book/', views.return_book, name='return_book'),
    path('member-progress/', views.admin_member_progress, name='admin_member_progress'),
    path('my-progress/', views.user_progress, name='user_progress'),
    path('api/member/<int:member_id>/details/', views.api_member_details, name='api_member_details'),
    path('api/rankings/', views.api_rankings, name='api_rankings'),
]
