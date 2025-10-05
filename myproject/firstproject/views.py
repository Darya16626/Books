from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import RegistrationForm


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("client_page")
    else:
        form = RegistrationForm()
    return render(request, "register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if user.email == "admin@example.com":
                    return redirect("admin_page")
                elif user.email == "manager@example.com":
                    return redirect("manager_page")
                else:
                    return redirect("client_page")
            else:
                form.add_error(None, "Неверный email или пароль")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

@login_required
def admin_page(request):
    if request.user.email != "admin@example.com":
        return HttpResponse("Доступ запрещён")
    return render(request, "admin_page.html")

@login_required
def manager_page(request):
    if request.user.email != "manager@example.com":
        return HttpResponse("Доступ запрещён")
    return render(request, "manager_page.html")

@login_required
def client_page(request):
    if request.user.email in ["admin@example.com", "manager@example.com"]:
        return redirect("info")
    return render(request, "client_page.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")
