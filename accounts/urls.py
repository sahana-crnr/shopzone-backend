from django.urls import path

from .views import LoginView, MeView, RegisterView, RefreshView, UserProfileUpdateView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("profile/", UserProfileUpdateView.as_view(), name="profile_update"),
]
