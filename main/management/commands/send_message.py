from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.urls import reverse
class Command(BaseCommand):
    help = 'Get product recommendations'

    def handle(self, *args, **kwargs):
        #send_mail('Subject', 'Message', 'andryuhaprohor@yandex.ru', ['tarjack2003@gmail.com'])
        reverse('mailagent:password_reset_confirm', kwargs={'uidb64': 'OQ', 'token': 'chyfec-05e6a7ae02adf31311399b8796b05f69'})