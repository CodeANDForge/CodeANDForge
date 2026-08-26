from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class ServiceType(models.Model):
    """A category of service offered by Code & Forge (e.g. Web Development)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    short_description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional icon keyword used by the template, e.g. 'code', 'app', 'custom'.",
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Service Type"
        verbose_name_plural = "Service Types"

    def __str__(self):
        return self.name


# Basic international-friendly phone/WhatsApp validator: digits, spaces, +, -
phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-]{7,20}$",
    message="أدخل رقم هاتف/واتساب صالح (أرقام فقط، ويمكن أن يبدأ بـ +).",
)


class ServiceRequest(models.Model):
    """A single inbound request submitted by a prospective client."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        IN_PROGRESS = "in_progress", "In Progress"
        CLOSED = "closed", "Closed"
        SPAM = "spam", "Marked as Spam"

    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="requests",
    )
    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=25, validators=[phone_validator])
    email = models.EmailField()
    project_description = models.TextField(max_length=4000)

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.NEW)

    # --- Security / anti-abuse metadata (never displayed to the public) ---
    submitted_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    honeypot_triggered = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.full_name} — {self.service_type} ({self.get_status_display()})"
