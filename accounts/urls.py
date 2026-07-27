from django.urls import path

from .views import (
    AddressDetailView,
    AddressListView,
    LoginView,
    MeView,
    RefreshView,
    RegisterView,
    SetDefaultAddressView,
    UserProfileUpdateView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("profile/", UserProfileUpdateView.as_view(), name="profile_update"),
    path("addresses/", AddressListView.as_view(), name="address_list"),
    path("addresses/<int:pk>/", AddressDetailView.as_view(), name="address_detail"),
    path("addresses/<int:pk>/default/", SetDefaultAddressView.as_view(), name="address_set_default"),
]
