from django.urls import path

from . import views

app_name = "services"

urlpatterns = [
    path("", views.home, name="home"),
    path("request-service/", views.request_service, name="request_service"),
    path("request-service/success/", views.request_success, name="request_success"),
]
