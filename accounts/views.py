from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import RegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("services:home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "تم إنشاء حسابك بنجاح!")
            return redirect("services:home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect("services:home")


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("services:home")
    login_form = None
    register_form = RegisterForm()
    from django.contrib.auth.forms import AuthenticationForm
    login_form = AuthenticationForm()
    return render(request, "accounts/landing.html", {
        "login_form": login_form,
        "register_form": register_form,
    })
