from django.urls import path
<<<<<<< HEAD
from .views import (
    UsersListCreateView,
    ForgotPasswordView,
    VerifyOTPView,
    ResetPasswordView,
    LogoutView,
    HealthView,
)

urlpatterns = [
    path("", HealthView.as_view()),
    path("users/", UsersListCreateView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("verify-otp/", VerifyOTPView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),
    path("logout/", LogoutView.as_view()),
=======

from .views import ForgotPasswordView, HealthView, LogoutView, ResetPasswordView, VerifyOtpView

urlpatterns = [
    path('', HealthView.as_view(), name='accounts-root'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='accounts-forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='accounts-reset-password'),
    path('verify-otp/', VerifyOtpView.as_view(), name='accounts-verify-otp'),
    path('logout/', LogoutView.as_view(), name='accounts-logout'),
>>>>>>> 47cfe8b92407e47beec70b77fffb36e33904f5d7
]
