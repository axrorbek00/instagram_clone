from django.urls import path
from .views import CreateUserView, VerifyCodeView, GetNewVerification, ChangeUserInformationView, ChangeUserPhotoView, \
    LoginView, LoginRefreshView, LogoutView, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('login/refresh/', LoginRefreshView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('signup/', CreateUserView.as_view()),
    path('verify/', VerifyCodeView.as_view()),
    path('new_verify/', GetNewVerification.as_view()),
    path('change_user/', ChangeUserInformationView.as_view()),
    path('change_user_photo/', ChangeUserPhotoView.as_view()),
    path('forgot_password/', ForgotPasswordView.as_view()),
    path('reset_password/', ResetPasswordView.as_view()),
]
