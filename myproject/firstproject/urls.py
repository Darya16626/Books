from django.urls import path
from .views import (
    login_view,
    logout_view,
    register_view,
    admin_page,
    manager_page,
    client_page,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("admin/", admin_page, name="admin_page"),
    path("manager/", manager_page, name="manager_page"),
    path("client/", client_page, name="client_page"),
]
