from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="login/", permanent=False)),  # редирект с корня на login/
    path("", include("firstproject.urls")),  # подключаем маршруты приложения
]
