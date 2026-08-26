from django.contrib import admin
from django.utils.html import format_html

from .models import ServiceRequest, ServiceType


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    """
    Admin view for incoming client requests.

    - All fields shown here are rendered through Django's admin templates,
      which auto-escape output, so even if a malicious string slipped past
      form sanitization it cannot execute as HTML/JS in the admin UI.
    - submitted_ip / user_agent / honeypot_triggered are read-only: they are
      forensic metadata, not something an admin should hand-edit.
    - Only staff/superusers with a valid session can reach this page at all,
      and it lives at the non-default, secret ADMIN_URL_PATH configured in
      settings.py / the environment.
    """

    list_display = (
        "id",
        "full_name",
        "service_type",
        "phone_number",
        "email",
        "status",
        "created_at",
        "whatsapp_link",
    )
    list_filter = ("status", "service_type", "created_at")
    search_fields = ("full_name", "email", "phone_number", "project_description")
    list_editable = ("status",)
    date_hierarchy = "created_at"
    readonly_fields = ("submitted_ip", "user_agent", "honeypot_triggered", "created_at", "updated_at")
    fieldsets = (
        ("بيانات العميل", {"fields": ("full_name", "phone_number", "email", "service_type")}),
        ("تفاصيل الطلب", {"fields": ("project_description", "status")}),
        ("بيانات الحماية (للاطلاع فقط)", {
            "classes": ("collapse",),
            "fields": ("submitted_ip", "user_agent", "honeypot_triggered", "created_at", "updated_at"),
        }),
    )

    def whatsapp_link(self, obj):
        digits = "".join(ch for ch in obj.phone_number if ch.isdigit())
        if not digits:
            return "-"
        return format_html(
            '<a href="https://wa.me/{}" target="_blank" rel="noopener noreferrer">تواصل واتساب</a>',
            digits,
        )

    whatsapp_link.short_description = "واتساب"

    def has_delete_permission(self, request, obj=None):
        # Only superusers may permanently delete a client's data.
        return request.user.is_superuser
