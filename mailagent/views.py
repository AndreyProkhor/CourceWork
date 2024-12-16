# mailagent/views.py

from users.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import CustomPasswordResetForm
from django.core.mail import EmailMessage
from django.utils.html import strip_tags
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from orders.models import Order
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import os
from django.conf import settings
from PIL import Image as PILImage
from urllib.parse import urljoin
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from orders.models import Order

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'mailagent/password_reset.html'
    email_template_name = 'mailagent/password_reset_email.html'
    success_url = reverse_lazy('mailagent:password_reset_done')
    subject_template_name = 'mailagent/password_reset_subject.txt'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = User.objects.filter(email=email).first()

        if not user:
            return self.form_invalid(form)

        subject = render_to_string(self.subject_template_name, {'user': user})
        subject = ''.join(subject.splitlines())
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        myjson = {
            'uidb64': uidb64,
            'email': user.email,
            'domain': self.request.get_host(),
            'site_name': 'VeloRecommend',
            'token': token,
            'protocol': 'https' if self.request.is_secure() else 'http',
        }
        reset_link = f"{myjson['protocol']}://{myjson['domain']}/mail/reset/{uidb64}/{token}/"
        myjson['reset_link'] = reset_link
        email_body_html = render_to_string(self.email_template_name, myjson)
        email = EmailMessage(
            subject,
            email_body_html,
            settings.EMAIL_HOST_USER,
            [user.email]
        )
        email.content_subtype = 'html'  
        email.send(fail_silently=False)

        return HttpResponseRedirect(self.get_success_url())


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'mailagent/password_reset_confirm.html'
    success_url = reverse_lazy('mailagent:password_reset_finally_done')

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Ваш пароль был успешно изменен.")
        return super().form_valid(form)


@login_required
@require_http_methods(["POST"])
def send_order_report(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        date_range = data.get('date_range', 'month')
        order_status = data.get('order_status', 'all')
        report_type = data.get('report_type', 'summary')

        print(f"Полученные данные: {data}")

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            print(f"Found user: {user.email}")
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        end_date = timezone.now()
        if date_range == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'week':
            start_date = end_date - timedelta(days=7)
        elif date_range == 'month':
            start_date = end_date - timedelta(days=30)
        elif date_range == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)

        print(f"Диапазон дат: {start_date} - {end_date}")

        orders = Order.objects.filter(user=user, created__range=(start_date, end_date))
        if order_status != 'all':
            orders = orders.filter(status=order_status)

        print(f"Найдено {orders.count()} заказов")

        total_orders = orders.count()
        total_amount = sum(order.get_total_cost() for order in orders)
        status_counts = {}
        for order in orders:
            status_counts[order.status] = status_counts.get(order.status, 0) + 1

        print(f"Статистика: {total_orders} заказы, общая сумма: {total_amount}")

        site_url = f"http://{request.get_host()}"

        context = {
            'user': user,
            'orders': orders,
            'total_orders': total_orders,
            'total_amount': total_amount,
            'status_counts': status_counts,
            'start_date': start_date,
            'end_date': end_date,
            'report_type': report_type,
            'site_url': site_url
        }

        if report_type == 'summary':
            template_name = 'mailagent/report_summary.html'
        else:
            template_name = 'mailagent/report_detailed.html'

        print(f"Using template: {template_name}")
        email_body = render_to_string(template_name, context)
        print(f"Email body length: {len(email_body)}")
        subject = f"Order Report for {user.email} ({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})"
        try:
            email = EmailMessage(
                subject=subject,
                body=email_body,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email]
            )
            email.content_subtype = 'html'
            print("Отправка сообщения...")
            email.send(fail_silently=False)
            print("Сообщение отправлено")
            return JsonResponse({'success': True, 'message': 'Report sent successfully'})
        except Exception as email_error:
            print(f"Ошибка при отправке сообщения: {email_error}")
            raise

    except Exception as e:
        import traceback
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print("Ошибка при отправке сообщения:", error_details)
        return JsonResponse({'error': str(e), 'details': error_details}, status=500)


@login_required
def search_users(request):
    query = request.GET.get('query', '').strip()
    if len(query) < 2:
        return JsonResponse({'error': 'Query too short'}, status=400)

    User = get_user_model()
    users = User.objects.filter(email__icontains=query)[:10]
    results = [{'id': user.id, 'email': user.email} for user in users]
    
    return JsonResponse(results, safe=False)


@login_required
@require_http_methods(["POST"])
def generate_report(request):
    User = get_user_model()
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        date_range = data.get('date_range', 'today')
        order_status = data.get('order_status', 'all')
        report_type = data.get('report_type', 'summary')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        end_date = timezone.now()
        if date_range == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'week':
            start_date = end_date - timedelta(days=7)
        elif date_range == 'month':
            start_date = end_date - timedelta(days=30)
        elif date_range == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # default to last 30 days
        print(order_status)
        orders = Order.objects.filter(user=user, created__range=(start_date, end_date))
        if order_status != 'all':
            orders = orders.filter(status=order_status)

        total_orders = orders.count()
        total_amount = sum(order.get_total_cost() for order in orders)
        status_counts = {}
        for order in orders:
            status_counts[order.status] = status_counts.get(order.status, 0) + 1

        context = {
            'user': user,
            'orders': orders,
            'total_orders': total_orders,
            'total_amount': total_amount,
            'status_counts': status_counts,
            'start_date': start_date,
            'end_date': end_date,
            'report_type': report_type
        }

        if report_type == 'summary':
            template_name = 'mailagent/report_summary.html'
        else:
            template_name = 'mailagent/report_detailed.html'

        preview_html = render_to_string(template_name, context)

        return JsonResponse({
            'preview': preview_html,
            'message': 'Report generated successfully'
        })

    except Exception as e:
        import traceback
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print("Ошибка при отправке сообщения:", error_details)
        return JsonResponse({'error': str(e), 'details': error_details}, status=500)