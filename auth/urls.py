from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    WmsTokenView,
    RegisterView,
    WorkstationLoginView,
    WorkstationLogoutView,
    RegisterWorkstationView
)

urlpatterns = [
    # JWT basic auth
    path("token/", WmsTokenView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Register
    path("register/", RegisterView.as_view(), name="register"),
    # Workstation flow
    path("workstation-login/", WorkstationLoginView.as_view(), name="workstation-login"),
    path("workstation-logout/", WorkstationLogoutView.as_view(), name="workstation-logout"),
    path("register-workstation/", RegisterWorkstationView.as_view(), name="register_workstation")
]
