from django.contrib import admin

from .models import MemberProfile, UserDailyUsage, UserSessionLog


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    ordering = ['-created_at']


@admin.register(UserSessionLog)
class UserSessionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time', 'session_duration_display', 'user_total_duration_display']
    list_filter = ['login_time', 'logout_time', 'user']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering = ['-login_time']
    readonly_fields = ['session_duration_display', 'user_total_duration_display', 'duration_seconds']
    date_hierarchy = 'login_time'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserDailyUsage)
class UserDailyUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'duration_display']
    list_filter = ['date', 'user']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering = ['-date', 'user__username']
    readonly_fields = ['user', 'date', 'duration_seconds', 'duration_display']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
