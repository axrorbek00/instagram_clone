from datetime import datetime
from tokenize import TokenError

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from shared.utility import send_email, check_user_type, check_email_or_phone
from .models import User, NEW, CODE_VERIFIED, DONE, VIA_EMAIL, VIA_PHONE
from .serializers import SignUpSerializer, ChangeUserInfoSerializer, ChangeUserPhotoSerializer, LoginSerializer, \
    LoginRefreshSerializer, LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound


class CreateUserView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = SignUpSerializer


class VerifyCodeView(APIView):  # codni tasdiqlash
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):

        user = self.request.user
        code = self.request.data.get('code')

        self.check_verify(user, code)
        return Response(
            data={
                "success": True,
                "auth_status": user.auth_status,
                "access_token": user.token()["access"],
                "refresh_token": user.token()["refresh_token"]
            }
        )

    @staticmethod
    def check_verify(user, code):
        verified = user.verify_codes.filter(expiration_time__gte=datetime.now(), code=code,
                                            # user.verify_codes, related name bilan boglangan
                                            is_confirmed=False)  # is_confirmed biror amalni tasdiqlashni bildradi
        if not verified.exists():
            data = {
                "message": "Tasdiqlash kodingiz xato yoki eskirgan"
            }
            raise ValidationError(data)
        else:
            verified.update(is_confirmed=True)

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()
        return True


class GetNewVerification(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        self.check_verification(user)
        if user.auth_type == VIA_EMAIL:
            code = user.customer.email(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
        else:
            data = {
                "message": "Email yoki telefon raqam notog'ri!"
            }
            raise ValidationError(data)
        return Response(
            {
                "success": True,
                "message": "Tasdiqlash kodingiz qaytadan jo'natildi"
            }
        )

    @staticmethod
    def check_verification(user):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_confirmed=False)
        if verifies.exists():
            data = {
                "message": "Kodingiz hali ishlatish uchun yaroqli. Biroz kuting!"
            }
            raise ValidationError(data)


class ChangeUserInformationView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangeUserInfoSerializer
    http_method_names = ['patch', 'put']

    def get_object(self):  # qaysi userni update qilmoqchiligimizni anqlaydi
        return self.request.user

    def update(self, request, *args, **kwargs):  # Put uchun hammasni ozgartiradi
        super(ChangeUserInformationView, self).update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': 'User updated successfully!',
            'auth_status': self.request.user.auth_status,
        }
        return Response(data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):  # Patch uchun 1 tasni ozgartiradi
        super(ChangeUserInformationView, self).partial_update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': 'User updated successfully!',
            'auth_status': self.request.user.auth_status,
        }
        return Response(data, status=status.HTTP_200_OK)


class ChangeUserPhotoView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        serializer = ChangeUserPhotoSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response(
                {
                    "message": "Rasim muvaffaqiyatli o'zgartirildi!"
                }, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(TokenObtainPairView):  # login qilyotgan userda tokenlar yoq wunga permission yozmadik
    serializer_class = LoginSerializer


class LoginRefreshView(TokenRefreshView):  # refresh tokeni olib access tokeni yanglaydi
    serializer_class = LoginRefreshSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data.get("refresh_token")
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                "success": True,
                "message": "You are logged out successfully!"
            }
            return Response(data, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            data = {
                "success": False,
                "message": "Invalid or expired refresh token."
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny, ]
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        email_or_phone = serializer.validated_data.get("email_or_phone")
        user = serializer.validated_data.get("user")
        if check_email_or_phone(email_or_phone) == "phone":
            code = user.create_verify_code(VIA_PHONE)
            send_email(email_or_phone, code)
        elif check_email_or_phone(email_or_phone) == "email":
            code = user.create_verify_code(VIA_EMAIL)
            send_email(email_or_phone, code)

        return Response(
            {
                "success": True,
                "message": "Tasdiqlash kodi muvaffaqiyatlik yuborildi!",
                "access": user.token()['access'],
                "refresh": user.token()['refresh_token'],
                "user_status": user.auth_status
            }, status=status.HTTP_200_OK
        )


class ResetPasswordView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ResetPasswordSerializer
    http_method_names = ["patch", "put"]

    def get_object(self):  # reset qilyotgan userni anqlash un
        return self.request.user  # request jonatgan user

    def update(self, request, *args, **kwargs):
        response = super(ResetPasswordView, self).update(request, *args, **kwargs)
        try:
            user = User.objects.get(id=response.data.get('id'))
        except ObjectDoesNotExist as e:
            raise NotFound(detail="User not found")

        return Response(
            {
                "success": True,
                "message": "Parolingiz muvaffaqiyatlik o'zgartirildi",
                "access": user.token()['access'],
                "refresh": user.token()['refresh_token']
            }, status=status.HTTP_200_OK
        )
