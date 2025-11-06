# authen/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from .models import Profile

@admin.action(description="Approve selected users")
def approve_selected(modeladmin, request, queryset):
    for profile in queryset.select_related("user"):
        profile.approval_status = "APPROVED"
        profile.save(update_fields=["approval_status"])
        profile.user.is_active = True
        profile.user.save(update_fields=["is_active"])

@admin.action(description="Reject selected users")
def reject_selected(modeladmin, request, queryset):
    for profile in queryset.select_related("user"):
        profile.approval_status = "REJECTED"
        profile.save(update_fields=["approval_status"])
        profile.user.is_active = False
        profile.user.save(update_fields=["is_active"])

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user_email", "user_is_active", "approval_status", "created_at")
    list_filter = ("approval_status", "user__is_active")
    search_fields = ("user__email", "user__username")
    actions = [approve_selected, reject_selected]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"

    def user_is_active(self, obj):
        return obj.user.is_active
    user_is_active.boolean = True
    user_is_active.short_description = "Is Active"
