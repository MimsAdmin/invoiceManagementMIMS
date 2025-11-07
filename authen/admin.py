# authen/admin.py
from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import format_html

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "approval_status_badge",
        "user_is_active",
        "created_at_formatted",
        "quick_actions",
    )
    list_filter = ("approval_status", "user__is_active", "created_at")
    search_fields = ("user__email", "user__username", "user__first_name", "user__last_name")
    date_hierarchy = "created_at"
    actions = None
    readonly_fields = ("created_at",)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def user_is_active(self, obj):
        return obj.user.is_active
    user_is_active.boolean = True
    user_is_active.short_description = "Active"
    user_is_active.admin_order_field = "user__is_active"

    def approval_status_badge(self, obj):
        colors = {"PENDING": "#fbbf24", "APPROVED": "#10b981", "REJECTED": "#ef4444"}
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:3px;'
            'font-weight:700;font-size:11px">{}</span>',
            colors.get(obj.approval_status, "#6b7280"),
            obj.get_approval_status_display(),
        )
    approval_status_badge.short_description = "Status"
    approval_status_badge.admin_order_field = "approval_status"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")
    created_at_formatted.short_description = "Created At"
    created_at_formatted.admin_order_field = "created_at"

    def quick_actions(self, obj):
        approve_url = reverse("admin:authen_profile_do", args=("approve", obj.pk))
        reject_url = reverse("admin:authen_profile_do", args=("reject", obj.pk))
        return format_html(
            '<a class="button" href="{}">Approve</a> '
            '<a class="button" href="{}">Reject</a>',
            approve_url, reject_url
        )
    quick_actions.short_description = "Quick Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "do/<str:action>/<int:pk>/",
                self.admin_site.admin_view(self._do_action),
                name="authen_profile_do",
            ),
        ]
        return custom + urls

    def _do_action(self, request, action: str, pk: int):
        """Approve/Reject via GET tanpa file tambahan."""
        profile = get_object_or_404(Profile, pk=pk)
        if action == "approve":
            profile.approval_status = "APPROVED"
            msg = f"{profile.user.email} approved & activated."
        elif action == "reject":
            profile.approval_status = "REJECTED"
            msg = f"{profile.user.email} rejected & deactivated."
        else:
            messages.error(request, "Unknown action.")
            return redirect("admin:authen_profile_changelist")

        profile.save()
        messages.success(request, msg)
        return redirect("admin:authen_profile_changelist")
