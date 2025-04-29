from django.contrib import admin

from .models import Report, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name", "email", "created_at")
    search_fields = ("username", "first_name", "last_name", "email")
    list_filter = ("is_active", "is_staff", "created_at")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    search_fields = ("title", "description", "user__username", "user__email")
    list_filter = ("created_at",)
