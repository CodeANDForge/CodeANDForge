from django.conf import settings
from django.contrib import admin
from django.urls import path, include

# The admin panel does NOT live at the predictable "/admin/" path.
# The real path is read from the environment (DJANGO_ADMIN_URL) so that
# automated scanners/bots probing "/admin/" get a plain 404 instead.
admin.site.site_header = "Code & Forge — Command Portal"
admin.site.site_title = "Code & Forge Admin"
admin.site.index_title = "Service Requests Overview"

urlpatterns = [
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("chat/", include("chat.urls")),
    path("", include("services.urls")),
]
