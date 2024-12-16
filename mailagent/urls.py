from django.urls import path
from .views import CustomPasswordResetView, CustomPasswordResetConfirmView, send_order_report, generate_report, search_users
from django.views.generic import TemplateView

app_name = 'mailagent'

urlpatterns = [
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', TemplateView.as_view(template_name='mailagent/password_reset_done.html'), name='password_reset_done'),
    path('password_reset/finally_done/', TemplateView.as_view(template_name='mailagent/password_reset_finally_done.html'), name='password_reset_finally_done'),
    path('api/send-order-report/', send_order_report, name='send_order_report'),
    path('generate-report/', generate_report, name='generate_report'),
    path('search-users/', search_users, name='search_users'),
]