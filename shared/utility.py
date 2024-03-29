import re
import threading
# import phonenumbers
from decouple import config
from twilio.rest import Client
# import phonenumbers
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

email_regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
phone_regex = re.compile(r'(\+[0-9]+\s*)?(\([0-9]+\))?[\s0-9\-]+[0-9]+')
username_regex = re.compile(r"^[a-zA-Z0-9_.-]+$")


def check_email_or_phone(email_phone_number):
    # phone_numbers = phonenumbers.parse(email_phone_number)
    if re.fullmatch(email_regex, email_phone_number):
        email_phone_number = 'email'

    elif re.fullmatch(phone_regex, email_phone_number):
        email_phone_number = 'phone'

    else:
        data = {
            'success': False,
            'message': 'Email yoki telefon raqamingiz notogri'
        }
        raise ValidationError(data)
    return email_phone_number


def check_user_type(user_input):
    if re.fullmatch(email_regex, user_input):
        user_input = 'email'
    elif re.fullmatch(phone_regex, user_input):
        user_input = 'phone'
    elif re.fullmatch(username_regex, user_input):
        user_input = 'username'
    else:
        data = {
            "success": False,
            "message": "Username, email yoki telefon raqamingiz notogri"
        }
        raise ValidationError(data)
    # raise ValidationError(f"User type must be 'email', 'phone', or 'username', not '{user_input}'")
    return user_input


class EmailThread(threading.Thread):  # asinxron tarzda bowqa tasklarga xalal bermagan xolda email jonatadi

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Email:  # hamma malumotlarni olib EmailThread ni ishga tushuradi

    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']]
        )
        if data.get('content_type') == 'html':
            email.content_subtype = 'html'
        EmailThread(email).start()


def send_email(email, code):  # code va emailni olib Email clasga jonatadi
    html_content = render_to_string(
        'email/authentication/activate_account.html',
        {'code': code}
    )
    Email.send_email(
        {
            "subject": "Ro'yxatdan o'tish",
            "to_email": email,
            "body": html_content,
            "content_type": "html"
        }
    )


def send_phone_code(phone_number, code):  # sms orqali code jonatiw un funksiya
    account_sid = config('account_sid')
    auth_token = config('auth_token')
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=f"Salom! sizning tasdiqlash kodingiz : {code}\n",
        from_="+9981234567",
        to=f'{phone_number}'
    )
