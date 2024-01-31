from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from shared.utility import check_email_or_phone, send_email, send_phone_code, check_user_type
from .models import User, UserConfirmation, VIA_EMAIL, VIA_PHONE, NEW, CODE_VERIFIED, DONE, PHOTO_DONE
from rest_framework import exceptions
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status'
        )
        extra_kwargs = {
            'auth_type': {'read_only': True, 'required': False},
            'auth_status': {'read_only': True, 'required': False}
        }

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)  # valid bolgan malumodan user yaratdi

        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)  # sms paket yoqligi un emailda jonatib turamiz
            # send_phone_code(user.phone_number, code)
        user.save()
        return user

    def validate(self, data):  # barcha filtlarni valid qiladi
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone(user_input)  # email or phone
        if input_type == "email":
            data = {
                "email": user_input,
                "auth_type": VIA_EMAIL
            }
        elif input_type == "phone":
            data = {
                "phone_number": user_input,
                "auth_type": VIA_PHONE
            }
        else:
            data = {
                'success': False,
                'message': "You must send email or phone number"
            }
            raise ValidationError(data)
        print('data', data)
        return data

    def validate_email_phone_number(self, value):  # email yoki nomerni valid qiladi
        value = value.lower()

        if value and User.objects.filter(email=value).exists():
            data = {
                'success': False,
                'message': 'Bu email allaqchon ishlatilgan'
            }
            raise ValidationError(data)

        if value and User.objects.filter(phone_number=value).exists():
            data = {
                'success': False,
                'message': 'Bu telefon raqami allaqchon ishlatilgan'
            }
            raise ValidationError(data)

        return value

    def to_representation(self, instance):  # tayor metod datani uwlab ozgartriw kirtib userga jonatadi
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data


class ChangeUserInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=True, write_only=True)
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        first_name = data.get('first_name', None)
        last_name = data.get('last_name', None)
        if password != confirm_password:
            raise ValidationError(
                {
                    "message": "Passwords don't match"
                }
            )
        if password:
            validate_password(password)  # validate_password, psswordni tekshradi
            validate_password(confirm_password)

        if first_name is not None and (len(first_name) > 25 or len(first_name) < 3):
            raise ValidationError(
                {
                    "message": "First name must be between 5 and 25 characters"
                }
            )

        if last_name is not None and (len(last_name) > 25 or len(last_name) < 3):
            raise ValidationError(
                {
                    "message": "Last name must be between 5 and 25 characters"
                }
            )

        if first_name is not None and first_name.isdigit() or last_name is not None and last_name.isdigit():
            raise ValidationError(
                {
                    "message": "This first name or last name is entirely numeric"
                }
            )
        return data

    def validate_username(self, username):
        if len(username) < 5 or len(username) > 25:
            raise ValidationError(
                {
                    "message": "Username must be between 5 and 25 characters"
                }
            )
        if username.isdigit():
            raise ValidationError(
                {
                    "message": "This username is entirely numeric"
                }
            )
        return username

    def update(self, instance, validated_data):  # instance user obyectlari, validated_data = user -
        instance.username = validated_data.get('username', instance.username)  # kirgizgan valid bolgan datalar
        instance.first_name = validated_data.get('first_name', instance.first_name)  # datadan kelgan malumotni brktr -
        instance.last_name = validated_data.get('last_name', instance.last_name)  # bolmasa random username qolsin
        instance.password = validated_data.get('password', instance.password)
        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))
        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE
        instance.save()
        return instance


class ChangeUserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(validators=[FileExtensionValidator(allowed_extensions=[
        'jpg', 'jpeg', 'png', 'heic', 'heif'
    ])])

    def update(self, instance, validated_data):
        photo = validated_data.get('photo')
        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_DONE
            instance.save()
        return instance


class LoginSerializer(TokenObtainPairSerializer):  # access va refresh token qaytaradi TokenObtainPairSerializer
    #

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['userinput'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)  # korinmas fild False un

    #

    def auth_validate(self, data):  # valid bolgan datalarni oladi
        user_input = data.get('userinput')  # email, phone_number, username
        if check_user_type(user_input) == 'username':
            username = user_input
        elif check_user_type(user_input) == "email":  # Anora@gmail.com   -> anOra@gmail.com
            user = self.get_user(email__iexact=user_input)  # user get method orqali user o'zgartiruvchiga biriktirildi
            username = user.username
        elif check_user_type(user_input) == 'phone':
            user = self.get_user(phone_number=user_input)  # bu  User.objects.get(phone_number=user_input) ga teng
            username = user.username
        else:
            data = {
                'success': True,
                'message': "Siz email, username yoki telefon raqami jonatishingiz kerak"
            }
            raise TypeError(data)

        authentication_kwargs = {  # username va parolni aniladik
            self.username_field: username,
            'password': data['password']
        }
        # user statusi tekshirilishi kerak
        current_user = User.objects.filter(username__iexact=username).first()  # None

        if current_user is not None and current_user.auth_status in [NEW, CODE_VERIFIED]:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Siz royhatdan toliq otmagansiz!"
                }
            )
        user = authenticate(**authentication_kwargs)  # username=usrname, password=data['password'] ga teng -
        if user is not None:  # buni yuqordan yozib qoyganmi,  authenticate da tekwramiz
            self.user = user
        else:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Sorry, login or password you entered is incorrect. Please check and trg again!"
                }
            )

    def validate(self, data):
        self.auth_validate(data)  # auth validan otgan userni beradi
        if self.user.auth_status not in [DONE, PHOTO_DONE]:  # wunga teng bolmasa
            raise PermissionDenied("Siz login qila olmaysiz. Ruxsatingiz yoq")
        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        data['full_name'] = self.user.full_name
        return data

    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError(
                {
                    "message": "No active account found"
                }
            )
        return users.first()


class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)  # foydalanuvchining oxirgi kirish vaqtini yangilash uchun update_last_login
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):  # write_only=true Post un boladi
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone', None)
        if email_or_phone is None:
            raise ValidationError(
                {
                    "success": False,
                    'message': "Email yoki telefon raqami kiritilishi shart!"
                }
            )
        user = User.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone))
        if not user.exists():
            raise NotFound(detail="User not found")
        attrs['user'] = user.first()
        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(min_length=8, required=True, write_only=True)
    confirm_password = serializers.CharField(min_length=8, required=True, write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "password",
            "confirm_password"
        )

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password != confirm_password:
            raise ValidationError(
                {
                    "success": False,
                    "message": "Parollaringiz qiymati teng emas"
                }
            )
        if password:
            validate_password(password)
        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance.set_password(password)
        return super(ResetPasswordSerializer, self).update(instance, validated_data)
