from django.urls import path

from .views import LoginView, MeView, RegisterView, RefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
]
