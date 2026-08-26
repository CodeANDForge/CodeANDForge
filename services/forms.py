import bleach
from django import forms
from django.core.exceptions import ValidationError

from .models import ServiceRequest, ServiceType


class ServiceRequestForm(forms.ModelForm):
    """
    Public-facing form used on the "Request a Service" page.

    Security notes:
    - Django's ModelForm validates every field against the model's
      validators/constraints (type, length, regex) BEFORE it ever touches
      the database, and the ORM only ever emits parameterized queries —
      so SQL injection is not possible through this form.
    - Every text field is run through `bleach.clean()` with an EMPTY
      allow-list, which strips all HTML/JS tags and attributes. Combined
      with Django's auto-escaping on output, this defends against both
      stored and reflected XSS.
    - A hidden honeypot field ("website") is added: real users never see
      or fill it (hidden with CSS), but simple spam bots that
      auto-fill every field will, so submissions with it non-empty are
      silently flagged/rejected.
    """

    # Honeypot field — must stay empty. Hidden via CSS in the template.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    service_type = forms.ModelChoiceField(
        queryset=ServiceType.objects.filter(is_active=True),
        empty_label="اختر نوع الخدمة...",
        label="نوع الخدمة",
        widget=forms.Select(attrs={"class": "neon-input"}),
    )

    class Meta:
        model = ServiceRequest
        fields = ["service_type", "full_name", "phone_number", "email", "project_description"]
        labels = {
            "full_name": "الاسم الكامل",
            "phone_number": "رقم الهاتف / واتساب",
            "email": "البريد الإلكتروني",
            "project_description": "وصف تفصيلي للطلب",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "neon-input",
                "placeholder": "مثال: أحمد الشمري",
                "autocomplete": "name",
                "maxlength": 120,
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "neon-input",
                "placeholder": "+966 5x xxx xxxx",
                "autocomplete": "tel",
                "maxlength": 25,
            }),
            "email": forms.EmailInput(attrs={
                "class": "neon-input",
                "placeholder": "you@example.com",
                "autocomplete": "email",
                "maxlength": 254,
            }),
            "project_description": forms.Textarea(attrs={
                "class": "neon-input",
                "placeholder": "صف مشروعك، أهدافه، والمدة الزمنية المطلوبة...",
                "rows": 6,
                "maxlength": 4000,
            }),
        }

    def clean_website(self):
        """Honeypot check: this field must always arrive empty."""
        value = self.cleaned_data.get("website", "")
        if value:
            # Do not reveal to the bot that it was caught — just reject.
            raise ValidationError("تعذر إرسال الطلب.")
        return value

    def _sanitize(self, value: str) -> str:
        """Strip ALL HTML/script content — defense in depth against XSS."""
        return bleach.clean(value, tags=[], attributes={}, strip=True).strip()

    def clean_full_name(self):
        name = self._sanitize(self.cleaned_data["full_name"])
        if len(name) < 2:
            raise ValidationError("الرجاء إدخال اسم صحيح.")
        return name

    def clean_project_description(self):
        description = self._sanitize(self.cleaned_data["project_description"])
        if len(description) < 10:
            raise ValidationError("الرجاء كتابة وصف أكثر تفصيلاً (10 أحرف على الأقل).")
        return description

    def clean_phone_number(self):
        return self._sanitize(self.cleaned_data["phone_number"])

    def clean_email(self):
        return self._sanitize(self.cleaned_data["email"]).lower()
