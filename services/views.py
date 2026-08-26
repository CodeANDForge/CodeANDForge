import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import mail_admins
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from .forms import ServiceRequestForm
from .models import ServiceType

logger = logging.getLogger("services")


def _client_ip(request):
    """Best-effort real client IP, respecting a trusted reverse proxy."""
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def home(request):
    """Public landing page — company intro + active services."""
    active_services = ServiceType.objects.filter(is_active=True)
    context = {
        "services": active_services,
        "facebook_url": settings.FACEBOOK_PAGE_URL,
    }
    return render(request, "services/home.html", context)


def ratelimited_error(request, exception):
    """
    Custom view rendered by django-ratelimit when a client exceeds the
    allowed submission rate. Returns HTTP 429 (Too Many Requests) rather
    than a generic 500/403, and never reveals internal rate-limit details.
    """
    logger.warning("Rate limit triggered for IP %s", _client_ip(request))
    return render(
        request,
        "services/rate_limited.html",
        {"facebook_url": settings.FACEBOOK_PAGE_URL},
        status=429,
    )


@csrf_protect
@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="5/h", method="POST", block=True)
def request_service(request):
    """
    "Request a Service" page.

    Protections applied:
    - @csrf_protect: Django's CSRF token is required on every POST
      (the {% csrf_token %} tag in the template supplies it). Requests
      without a valid, matching token are rejected with HTTP 403.
    - @ratelimit(key="ip", rate="5/h", ...): a single IP address may submit
      at most 5 requests per hour. Further POSTs return HTTP 429 via
      `ratelimited_error` above — this stops scripted spam/flood attempts.
    - ServiceRequestForm sanitizes and validates every field (see forms.py),
      including a hidden honeypot trap for simple bots.
    - The ORM (ServiceRequest.objects.create via form.save()) uses
      parameterized queries exclusively, so SQL injection is not possible.
    """
    if request.method == "POST":
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.submitted_ip = _client_ip(request)
            service_request.user_agent = request.META.get("HTTP_USER_AGENT", "")[:300]
            service_request.save()

            logger.info(
                "New service request #%s from %s (%s)",
                service_request.pk,
                service_request.full_name,
                service_request.email,
            )

            if settings.ADMIN_NOTIFICATION_EMAIL:
                try:
                    mail_admins(
                        subject=f"طلب خدمة جديد — {service_request.service_type}",
                        message=(
                            f"الاسم: {service_request.full_name}\n"
                            f"الهاتف: {service_request.phone_number}\n"
                            f"البريد: {service_request.email}\n"
                            f"الخدمة: {service_request.service_type}\n\n"
                            f"الوصف:\n{service_request.project_description}"
                        ),
                        fail_silently=True,
                    )
                except Exception:
                    logger.exception("Failed to send admin notification email")

            messages.success(request, "تم استلام طلبك بنجاح! سنتواصل معك قريباً.")
            return redirect("services:request_success")
        # Invalid form: fall through and re-render with field errors.
    else:
        form = ServiceRequestForm()

    return render(request, "services/service_request.html", {"form": form})


def request_success(request):
    return render(
        request,
        "services/request_success.html",
        {"facebook_url": settings.FACEBOOK_PAGE_URL},
    )
